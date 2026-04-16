# A script a NAV Online Pénztárgép (OPF) rendszeréből kérdezi le egy gép aktuális státuszát.

import requests
import hashlib
import uuid
from datetime import datetime, timezone
from lxml import etree
from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER, CASHREGISTER_ID, NAV_TEST_SIGNATURE_KEY, NAV_TEST_PASSWORD, NAV_TEST_USERNAME

teszt = 0

# creds:

API_URL = "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus"
if teszt == 1:
	NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, 
	API_URL = "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus"
	NAV_SIGNATURE_KEY = NAV_TEST_SIGNATURE_KEY
	NAV_PASSWORD = NAV_TEST_PASSWORD
	NAV_USERNAME = NAV_TEST_USERNAME



SOFTWARE_ID = "HU10772335AU-00003"
SOFTWARE_NAME = "ARSUNA status checker"
SOFTWARE_VERSION = "1.0"
SOFTWARE_DEV_NAME = "Kovács Krisztián - Gemini 3.1 Pro"
SOFTWARE_DEV_CONTACT = "it@arsuna.hu"

# --- FÜGGVÉNYEK ---

def get_utc_timestamp_str() -> str:
	"""Visszaadja a jelenlegi időt UTC-ben, a NAV által kért formátumban."""
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def get_signature_timestamp_str() -> str:
	"""Visszaadja a jelenlegi időt UTC-ben a requestSignature-höz szükséges formátumban."""
	return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

def create_password_hash(password: str) -> str:
	"""
	Létrehozza a jelszó hash-t a dokumentáció szerint (SHA-512).
	Csak a kapott hash hexadecimális kódját nagybetűsítjük!
	"""
	sha512 = hashlib.sha512()
	sha512.update(password.encode('utf-8'))
	return sha512.hexdigest().upper()

def create_request_signature(request_id: str, timestamp_str: str, signing_key: str) -> str:
	"""
	Létrehozza a kérés aláírását (requestSignature) a dokumentáció szerint (SHA3-512).
	"""
	concatenated_string = f"{request_id}{timestamp_str}{signing_key}"
	sha3_512 = hashlib.sha3_512()
	sha3_512.update(concatenated_string.encode('utf-8'))
	return sha3_512.hexdigest().upper()

def build_soap_xml_request(request_id: str, timestamp_utc: str, password_hash: str, request_signature: str, ap_number: str) -> str:
	"""
	Felépíti a SOAP XML kérést a megadott adatokból.
	"""
	nsmap = {
		"soap": "http://www.w3.org/2003/05/soap-envelope",
		"api": "http://schemas.nav.gov.hu/OPF/1.0/api",
		"com": "http://schemas.nav.gov.hu/NTCA/1.0/common"
	}

	envelope = etree.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope", nsmap=nsmap)
	etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Header")
	body = etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")

	request_node = etree.SubElement(body, "{http://schemas.nav.gov.hu/OPF/1.0/api}QueryCashRegisterStatusRequest")

	# Header
	header = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}header")
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestId").text = request_id
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}timestamp").text = timestamp_utc
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestVersion").text = "1.0"
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}headerVersion").text = "1.0"

	# User
	user = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}user")
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}login").text = NAV_USERNAME
	
	pwd_hash_element = etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}passwordHash", cryptoType="SHA-512")
	pwd_hash_element.text = password_hash
	
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}taxNumber").text = NAV_TAX_NUMBER
	
	req_sig_element = etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestSignature", cryptoType="SHA3-512")
	req_sig_element.text = request_signature

	# Software
	software = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}software")
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareId").text = SOFTWARE_ID
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareName").text = SOFTWARE_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareOperation").text = "LOCAL_SOFTWARE"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareMainVersion").text = SOFTWARE_VERSION
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevName").text = SOFTWARE_DEV_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevContact").text = SOFTWARE_DEV_CONTACT
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevCountryCode").text = "HU"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevTaxNumber").text = NAV_TAX_NUMBER

	# Query params
	status_query = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}cashRegisterStatusQuery")
	ap_list = etree.SubElement(status_query, "{http://schemas.nav.gov.hu/OPF/1.0/api}APNumberList")
	etree.SubElement(ap_list, "{http://schemas.nav.gov.hu/OPF/1.0/api}APNumber").text = ap_number

	return etree.tostring(envelope, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode('utf-8')

def parse_mtom_status_response(response: requests.Response):
	"""Kibontja az MTOM borítékot és feldolgozza a státusz válasz XML-t."""
	content_type = response.headers.get('Content-Type', '')
	
	# Próbáljuk megkeresni a határolót (boundary) a fejlécben...
	boundary = None
	for part in content_type.split(';'):
		if 'boundary=' in part.lower():
			# Kiszedjük az egyenlőségjel utáni részt és leszedjük az idézőjeleket
			boundary = part.strip().split('=', 1)[1].strip('"').strip("'")
			break
			
	# ...ha nincs a fejlécben, kinyerjük magából a letöltött nyers szöveg első sorából!
	if not boundary:
		first_line = response.text.lstrip().split('\n')[0].strip()
		if first_line.startswith('--'):
			boundary = first_line[2:] # Levágjuk a két kötőjelet az elejéről
			
	if not boundary:
		print("Hiba: Nem található 'boundary' a fejlécben vagy a válaszban.")
		return

	# Válasz darabolása a boundary mentén
	parts = response.content.split(f'--{boundary}'.encode('utf-8'))

	for part in parts:
		if not part.strip() or part.strip() == b'--':
			continue

		try:
			# A part fejléce és az XML tartalma közötti dupla sortörés keresése
			if b'\r\n\r\n' in part:
				header_bytes, content = part.split(b'\r\n\r\n', 1)
			elif b'\n\n' in part:
				header_bytes, content = part.split(b'\n\n', 1)
			else:
				continue
				
			headers = header_bytes.decode('utf-8').lower()
		except ValueError:
			continue

		# Ha megtaláltuk az XML részt (application/xop+xml)
		if 'xml' in headers:
			try:
				# Szóközök és sortörések lecsípése
				content = content.strip()
				xml_response_root = etree.fromstring(content)
				
				# A NAV által használt névterek definiálása
				ns = {
					'env': 'http://www.w3.org/2003/05/soap-envelope',
					'ns2': 'http://schemas.nav.gov.hu/NTCA/1.0/common',
					'ns3': 'http://schemas.nav.gov.hu/OPF/1.0/api'
				}

				print("\n✅ --- Szerver Válasz Sikeresen Feldolgozva ---")
				
				# Funkció kód ellenőrzése
				func_code_node = xml_response_root.find('.//ns2:funcCode', namespaces=ns)
				if func_code_node is not None:
					if func_code_node.text == "ERROR":
						err_code = xml_response_root.find('.//ns2:errorCode', namespaces=ns)
						err_msg = xml_response_root.find('.//ns2:message', namespaces=ns)
						print(f"❌ NAV HIBA ({err_code.text if err_code is not None else '?'})")
						print(f"Üzenet: {err_msg.text if err_msg is not None else 'Ismeretlen hiba'}")
						return
					else:
						print(f"Lekérdezés státusza: {func_code_node.text}")

				# Státusz adatok kinyerése
				status_nodes = xml_response_root.findall('.//ns3:cashRegisterStatus', namespaces=ns)
				if status_nodes:
					print("\n📊 --- Pénztárgép Adatai ---")
					for status_node in status_nodes:
						ap_num = status_node.find('ns3:APNumber', namespaces=ns)
						last_comm = status_node.find('ns3:lastCommunicationDate', namespaces=ns)
						min_file = status_node.find('ns3:minAvailableFileNumber', namespaces=ns)
						max_file = status_node.find('ns3:maxAvailableFileNumber', namespaces=ns)
						
						ap_text = ap_num.text if ap_num is not None else "Ismeretlen"
						last_comm_text = last_comm.text if last_comm is not None else "Nincs adat"
						
						# Megjelenítés
						print(f"  AP Szám:			   {ap_text}")
						print(f"  Utolsó kommunikáció:   {last_comm_text}")
						if min_file is not None and max_file is not None:
							print(f"  Elérhető naplófájlok:  {min_file.text} - {max_file.text}")
						else:
							print("  Elérhető naplófájlok:  Nincs letölthető napló.")
				else:
					print("Sikeres kérés, de nem található pénztárgép adat a válaszban.")

			except etree.XMLSyntaxError as e:
				print(f"XML elemzési hiba a kibontott részben: {e}")
# --- FŐ PROGRAM ---
if __name__ == "__main__":
	print("NAV Pénztárgép státusz lekérdező script indul...")

	# 1. Kérés egyedi azonosító generálása (max 30 karakter)
	request_id = f"RID_{uuid.uuid4().hex[:20].upper()}"
	print(f"Request ID: {request_id}")

	# 2. Időbélyegek generálása
	timestamp_for_xml = get_utc_timestamp_str()
	timestamp_for_sig = get_signature_timestamp_str()
	
	# 3. Hashek kiszámítása
	password_h = create_password_hash(NAV_PASSWORD)
	request_sig = create_request_signature(request_id, timestamp_for_sig, NAV_SIGNATURE_KEY)

	# 4. XML kérés összeállítása
	xml_payload = build_soap_xml_request(request_id, timestamp_for_xml, password_h, request_sig, CASHREGISTER_ID)
	
	print("\n--- Elküldendő XML Kérés ---")
	print(xml_payload)
	print("--------------------------\n")

	# 5. HTTP kérés elküldése
	headers = {
		'Content-Type': 'application/soap+xml; charset=utf-8',
		'Accept': 'multipart/related, application/soap+xml',
		'User-Agent': 'Arsuna-Status-Checker/1.0'
	}
	
	try:
		print(f"Kérés küldése a(z) {API_URL} végpontra...")
		response = requests.post(API_URL, data=xml_payload.encode('utf-8'), headers=headers, timeout=30)
		
		print(f"\nVálasz érkezett. HTTP státuszkód: {response.status_code}")
		
		# 6. Válasz feldolgozása
		if response.status_code == 200:
			parse_mtom_status_response(response)

	except requests.exceptions.RequestException as e:
		print(f"Hálózati hiba történt: {e}")