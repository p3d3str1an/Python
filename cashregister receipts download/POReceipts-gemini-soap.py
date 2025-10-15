import requests
import hashlib
import uuid
from datetime import datetime, timezone
from lxml import etree
import os

# ===== Konfiguráció =====
ENV = "prod"  # "test" vagy "prod"

if ENV== "test":
	from credentials import NAV_TEST_SIGNATURE_KEY as ALAIROKULCS, NAV_TEST_PASSWORD as JELSZO, NAV_TEST_USERNAME as FELHASZNALONEV, NAV_TAX_NUMBER as ADOSZAM, CASHREGISTER_ID
	API_URL = "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"
else:
	from credentials import NAV_SIGNATURE_KEY as ALAIROKULCS, NAV_PASSWORD as JELSZO, NAV_USERNAME as FELHASZNALONEV, NAV_TAX_NUMBER as ADOSZAM, CASHREGISTER_ID
	API_URL = "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"

SOFTWARE_ID = "HU10772335AU-AU-R001"
SOFTWARE_NAME = "ARSUNA receipts downloader gemini"
SOFTWARE_VERSION = "1.0"
SOFTWARE_DEV_NAME = "Kovács Krisztián - Gemini 2.5 pro"
SOFTWARE_DEV_CONTACT = "it@arsuna.hu"

# --- FÜGGVÉNYEK (a hashelés nem változott) ---
def get_utc_timestamp_str() -> str:
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def get_signature_timestamp_str() -> str:
	return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

def create_password_hash(password: str) -> str:
	sha512 = hashlib.sha512()
	sha512.update(password.upper().encode('utf-8'))
	return sha512.hexdigest().upper()

def create_request_signature(request_id: str, timestamp_str: str, signing_key: str) -> str:
	concatenated_string = f"{request_id}{timestamp_str}{signing_key}"
	sha3_512 = hashlib.sha3_512()
	sha3_512.update(concatenated_string.encode('utf-8'))
	return sha3_512.hexdigest().upper()

def build_soap_request(request_id: str, timestamp_utc: str, password_hash: str, request_signature: str) -> str:
	"""
	Felépíti a teljes SOAP XML kérést, borítékkal együtt.
	"""
	# Névterek definiálása
	ns_soap = "http://www.w3.org/2003/05/soap-envelope"
	ns_base = "http://schemas.nav.gov.hu/OPF/1.0/cashregister"
	ns_common = "http://schemas.nav.gov.hu/NTCA/1.0/common"
	ns_api = "http://schemas.nav.gov.hu/OSA/3.0/api"

	# 1. A belső adat XML (a tényleges kérés) felépítése
	request_content_root = etree.Element(f"{{{ns_base}}}QueryCashRegisterFileRequest")

	# Header
	header = etree.SubElement(request_content_root, f"{{{ns_common}}}header")
	etree.SubElement(header, f"{{{ns_common}}}requestId").text = request_id
	etree.SubElement(header, f"{{{ns_common}}}timestamp").text = timestamp_utc
	etree.SubElement(header, f"{{{ns_common}}}requestVersion").text = "1.0"
	etree.SubElement(header, f"{{{ns_common}}}headerVersion").text = "1.0"

	# User
	user = etree.SubElement(request_content_root, f"{{{ns_common}}}user")
	etree.SubElement(user, f"{{{ns_common}}}login").text = FELHASZNALONEV
	pwd_hash_element = etree.SubElement(user, f"{{{ns_common}}}passwordHash", cryptoType="SHA-512")
	pwd_hash_element.text = password_hash
	etree.SubElement(user, f"{{{ns_common}}}taxNumber").text = ADOSZAM
	req_sig_element = etree.SubElement(user, f"{{{ns_common}}}requestSignature", cryptoType="SHA3-512")
	req_sig_element.text = request_signature

	# Software
	software = etree.SubElement(request_content_root, f"{{{ns_api}}}software")
	etree.SubElement(software, "softwareId").text = SOFTWARE_ID
	etree.SubElement(software, "softwareName").text = SOFTWARE_NAME
	etree.SubElement(software, "softwareOperation").text = "LOCAL_SOFTWARE"
	etree.SubElement(software, "softwareMainVersion").text = SOFTWARE_VERSION
	etree.SubElement(software, "softwareDevName").text = SOFTWARE_DEV_NAME
	etree.SubElement(software, "softwareDevContact").text = SOFTWARE_DEV_CONTACT
	
	# Lekérdezés specifikus adatai
	file_query_params = etree.SubElement(request_content_root, f"{{{ns_base}}}cashRegisterFileQuery")
	etree.SubElement(file_query_params, "cashRegisterId").text = CASHREGISTER_ID
	etree.SubElement(file_query_params, "fromNumber").text = "1" # <- CSERÉLD KI A KEZDŐ SORSZÁMRA
	etree.SubElement(file_query_params, "toNumber").text = "1"   # <- CSERÉLD KI A ZÁRÓ SORSZÁMRA

	# 2. A SOAP boríték létrehozása és a belső XML beágyazása
	NSMAP = {
		"soapenv": ns_soap,
		"base": ns_base,
		"common": ns_common,
		"api": ns_api
	}
	envelope = etree.Element(f"{{{ns_soap}}}Envelope", nsmap=NSMAP)
	body = etree.SubElement(envelope, f"{{{ns_soap}}}Body")
	body.append(request_content_root) # A teljes belső XML-t ide illesztjük

	# A teljes SOAP üzenet visszaadása stringként, XML deklarációval
	return etree.tostring(envelope, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode('utf-8')

def parse_mtom_response(response: requests.Response):
	"""Feldolgozza a többrészes MTOM választ. (Változatlan maradt)"""
	if 'multipart/related' not in response.headers.get('Content-Type', ''):
		print("Hiba: A válasz nem a várt multipart/related formátumú.")
		print("Válasz tartalma:")
		print(response.text)
		return

	content_type_parts = response.headers['Content-Type'].split(';')
	boundary = next((part.strip().split('=')[1].strip('"') for part in content_type_parts if 'boundary=' in part), None)
	if not boundary:
		print("Hiba: Nem található a 'boundary' a Content-Type headerben.")
		return

	parts = response.content.split(f'--{boundary}'.encode('utf-8'))
	for part in parts:
		if not part.strip(): continue
		try:
			header_bytes, content = part.split(b'\r\n\r\n', 1)
			headers = header_bytes.decode('utf-8')
		except ValueError: continue
		if 'application/xop+xml' in headers:
			print("--- XML Válasz Feldolgozása ---")
			# A SOAP válaszban a releváns rész a Body-ban van, így arra kell keresni
			xml_soap_root = etree.fromstring(content)
			result_node = xml_soap_root.find('.//{http://schemas.nav.gov.hu/OPF/1.0/cashregister}result')
			if result_node is not None:
				func_code = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}funcCode').text
				print(f"Funkció kód: {func_code}")
				if func_code == "ERROR":
					error_code = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}errorCode').text
					message = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}message').text
					print(f"Hibakód: {error_code}")
					print(f"Üzenet: {message}")
			else: print("Nem található 'result' elem a SOAP Body-ban.")
		if 'Content-Transfer-Encoding: binary' in headers:
			content_id_header = next((h for h in headers.split('\r\n') if h.lower().startswith('content-id:')), None)
			if content_id_header:
				content_id = content_id_header.split(':', 1)[1].strip().strip('<>')
				file_name = f"naplo_{content_id}.zip"
				print(f"\n--- Bináris Fájl Mentése ---")
				print(f"Talált naplófájl, mentés '{file_name}' néven...")
				with open(file_name, 'wb') as f:
					f.write(content.strip(b'\r\n--'))
				print(f"'{file_name}' sikeresen mentve. Méret: {os.path.getsize(file_name)} bájt.")


# --- FŐ PROGRAM ---
if __name__ == "__main__":
	print("NAV naplóállomány lekérdező script indul (SOAP borítékkal)...")
	request_id = f"RID_{str(uuid.uuid4()).upper()}"
	timestamp_for_xml = get_utc_timestamp_str()
	timestamp_for_sig = get_signature_timestamp_str()
	password_h = create_password_hash(JELSZO)
	request_sig = create_request_signature(request_id, timestamp_for_sig, ALAIROKULCS)

	# A teljes SOAP kérés előállítása
	soap_payload = build_soap_request(request_id, timestamp_for_xml, password_h, request_sig)
	
	print("\n--- Elküldendő SOAP Kérés ---")
	print(soap_payload)
	print("--------------------------\n")

	# A HTTP header módosítása a SOAP szabványnak megfelelően
	headers = {
		'Content-Type': 'application/soap+xml; charset=utf-8',
		'Accept': 'application/xml, multipart/related' # Jelzizzük, hogy mindkettőt el tudjuk fogadni
	}
	
	try:
		body=soap_payload.encode('utf-8')
		print(f"Kérés küldése a(z) {API_URL} végpontra...")
		response = requests.post(API_URL, data=body, timeout=30)
		
		print(f"Válasz érkezett. HTTP státuszkód: {response.status_code}")
		
		if response.status_code == 200:
			parse_mtom_response(response)
		else:
			print("Hiba történt a kérés során:")
			# A NAV gyakran XML-ben küld hibaüzenetet, még nem 200-as státuszkód esetén is
			print(response.text)

	except requests.exceptions.RequestException as e:
		print(f"Hálózati hiba történt: {e}")