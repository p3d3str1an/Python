#Vibe coded with Gemini
#letölti az elérhető pénztárgépnapló fájlokat

import requests
import hashlib
import uuid
from datetime import datetime, timezone
from lxml import etree
import os
from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER, CASHREGISTER_ID, NAV_TEST_SIGNATURE_KEY, NAV_TEST_PASSWORD, NAV_TEST_USERNAME, KOZOSPATH

# --- KONFIGURÁCIÓ ---
# Állítsd 'TEST'-re vagy 'PROD'-ra!
ENV = "PROD" 

# Ide menti a letöltött ZIP fájlokat (ha nem létezik, létrehozza)
TARGET_FOLDER = KOZOSPATH + r"\PÉNZÜGY\BEOLVASÓK\Pénztárgép\zip"

if ENV == "TEST":
	USERNAME = NAV_TEST_USERNAME
	PASSWORD = NAV_TEST_PASSWORD
	SIGNATURE_KEY = NAV_TEST_SIGNATURE_KEY
	STATUS_URL = "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus"
	FILE_URL = "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"
	print(f"--- TESZT KÖRNYEZET AKTÍV ({USERNAME}) ---")
else:
	USERNAME = NAV_USERNAME
	PASSWORD = NAV_PASSWORD
	SIGNATURE_KEY = NAV_SIGNATURE_KEY
	STATUS_URL = "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus"
	FILE_URL = "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"
	print(f"--- ÉLES KÖRNYEZET AKTÍV ({USERNAME}) ---")

# --- SZOFTVER ADATOK ---
SOFTWARE_ID = "123456789123456789"
SOFTWARE_NAME = "ARSUNA receipts downloader"
SOFTWARE_VERSION = "1.0"
SOFTWARE_DEV_NAME = "Kovács Krisztián - Gemini 3.1 Pro"
SOFTWARE_DEV_CONTACT = "it@arsuna.hu"

# --- Mappa előkészítése ---
os.makedirs(TARGET_FOLDER, exist_ok=True)
print(f"📁 Célmappa beállítva: {os.path.abspath(TARGET_FOLDER)}")


# --- SEGÉDFÜGGVÉNYEK ---

def get_utc_timestamp_str() -> str:
	return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def get_signature_timestamp_str() -> str:
	return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

def create_password_hash(password: str) -> str:
	sha512 = hashlib.sha512()
	sha512.update(password.encode('utf-8'))
	return sha512.hexdigest().upper()

def create_request_signature(request_id: str, timestamp_str: str, signing_key: str) -> str:
	concatenated_string = f"{request_id}{timestamp_str}{signing_key}"
	sha3_512 = hashlib.sha3_512()
	sha3_512.update(concatenated_string.encode('utf-8'))
	return sha3_512.hexdigest().upper()


# --- XML ÉPÍTŐ FÜGGVÉNYEK ---

def build_status_xml_request(request_id: str, timestamp_utc: str, password_hash: str, request_signature: str, ap_number: str) -> str:
	nsmap = {
		"soap": "http://www.w3.org/2003/05/soap-envelope",
		"api": "http://schemas.nav.gov.hu/OPF/1.0/api",
		"com": "http://schemas.nav.gov.hu/NTCA/1.0/common"
	}
	envelope = etree.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope", nsmap=nsmap)
	etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Header")
	body = etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
	request_node = etree.SubElement(body, "{http://schemas.nav.gov.hu/OPF/1.0/api}QueryCashRegisterStatusRequest")

	header = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}header")
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestId").text = request_id
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}timestamp").text = timestamp_utc
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestVersion").text = "1.0"
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}headerVersion").text = "1.0"

	user = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}user")
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}login").text = USERNAME
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}passwordHash", cryptoType="SHA-512").text = password_hash
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}taxNumber").text = NAV_TAX_NUMBER
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestSignature", cryptoType="SHA3-512").text = request_signature

	software = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}software")
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareId").text = SOFTWARE_ID
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareName").text = SOFTWARE_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareOperation").text = "LOCAL_SOFTWARE"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareMainVersion").text = SOFTWARE_VERSION
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevName").text = SOFTWARE_DEV_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevContact").text = SOFTWARE_DEV_CONTACT
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevCountryCode").text = "HU"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevTaxNumber").text = NAV_TAX_NUMBER

	status_query = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}cashRegisterStatusQuery")
	ap_list = etree.SubElement(status_query, "{http://schemas.nav.gov.hu/OPF/1.0/api}APNumberList")
	etree.SubElement(ap_list, "{http://schemas.nav.gov.hu/OPF/1.0/api}APNumber").text = ap_number

	return etree.tostring(envelope, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode('utf-8')


def build_file_download_xml_request(request_id: str, timestamp_utc: str, password_hash: str, request_signature: str, ap_number: str, file_start: str, file_end: str) -> str:
	nsmap = {
		"soap": "http://www.w3.org/2003/05/soap-envelope",
		"api": "http://schemas.nav.gov.hu/OPF/1.0/api",
		"com": "http://schemas.nav.gov.hu/NTCA/1.0/common"
	}
	envelope = etree.Element("{http://www.w3.org/2003/05/soap-envelope}Envelope", nsmap=nsmap)
	etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Header")
	body = etree.SubElement(envelope, "{http://www.w3.org/2003/05/soap-envelope}Body")
	request_node = etree.SubElement(body, "{http://schemas.nav.gov.hu/OPF/1.0/api}QueryCashRegisterFileDataRequest")

	header = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}header")
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestId").text = request_id
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}timestamp").text = timestamp_utc
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestVersion").text = "1.0"
	etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}headerVersion").text = "1.0"

	user = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/NTCA/1.0/common}user")
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}login").text = USERNAME
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}passwordHash", cryptoType="SHA-512").text = password_hash
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}taxNumber").text = NAV_TAX_NUMBER
	etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestSignature", cryptoType="SHA3-512").text = request_signature

	software = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}software")
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareId").text = SOFTWARE_ID
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareName").text = SOFTWARE_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareOperation").text = "LOCAL_SOFTWARE"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareMainVersion").text = SOFTWARE_VERSION
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevName").text = SOFTWARE_DEV_NAME
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevContact").text = SOFTWARE_DEV_CONTACT
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevCountryCode").text = "HU"
	etree.SubElement(software, "{http://schemas.nav.gov.hu/OPF/1.0/api}softwareDevTaxNumber").text = NAV_TAX_NUMBER

	file_query = etree.SubElement(request_node, "{http://schemas.nav.gov.hu/OPF/1.0/api}cashRegisterFileDataQuery")
	etree.SubElement(file_query, "{http://schemas.nav.gov.hu/OPF/1.0/api}APNumber").text = ap_number
	etree.SubElement(file_query, "{http://schemas.nav.gov.hu/OPF/1.0/api}fileNumberStart").text = str(file_start)
	etree.SubElement(file_query, "{http://schemas.nav.gov.hu/OPF/1.0/api}fileNumberEnd").text = str(file_end)

	return etree.tostring(envelope, pretty_print=True, xml_declaration=False, encoding='UTF-8').decode('utf-8')


# --- VÁLASZ FELDOLGOZÓ FÜGGVÉNYEK ---

def extract_boundary(content_type: str, response_text: str) -> str:
	boundary = None
	for part in content_type.split(';'):
		if 'boundary=' in part.lower():
			boundary = part.strip().split('=', 1)[1].strip('"').strip("'")
			break
	if not boundary:
		first_line = response_text.lstrip().split('\n')[0].strip()
		if first_line.startswith('--'):
			boundary = first_line[2:]
	return boundary

def parse_status_response(response: requests.Response):
	content_type = response.headers.get('Content-Type', '')
	boundary = extract_boundary(content_type, response.text)
	
	if not boundary:
		print("Hiba: Nem található 'boundary' a státusz válaszban.")
		return None, None

	parts = response.content.split(f'--{boundary}'.encode('utf-8'))
	
	for part in parts:
		if not part.strip() or part.strip() == b'--':
			continue

		try:
			if b'\r\n\r\n' in part:
				header_bytes, content = part.split(b'\r\n\r\n', 1)
			elif b'\n\n' in part:
				header_bytes, content = part.split(b'\n\n', 1)
			else:
				continue
			headers = header_bytes.decode('utf-8').lower()
		except ValueError:
			continue

		if 'xml' in headers:
			try:
				xml_response_root = etree.fromstring(content.strip())
				ns = {
					'ns2': 'http://schemas.nav.gov.hu/NTCA/1.0/common',
					'ns3': 'http://schemas.nav.gov.hu/OPF/1.0/api'
				}
				
				func_code_node = xml_response_root.find('.//ns2:funcCode', namespaces=ns)
				if func_code_node is not None and func_code_node.text == "ERROR":
					err_msg = xml_response_root.find('.//ns2:message', namespaces=ns)
					print(f"❌ NAV HIBA a státusz lekérdezésnél: {err_msg.text if err_msg is not None else 'Ismeretlen'}")
					return None, None

				status_node = xml_response_root.find('.//ns3:cashRegisterStatus', namespaces=ns)
				if status_node is not None:
					min_file = status_node.find('ns3:minAvailableFileNumber', namespaces=ns)
					max_file = status_node.find('ns3:maxAvailableFileNumber', namespaces=ns)
					
					if min_file is not None and max_file is not None:
						print(f"📊 Talált naplófájlok: {min_file.text} - {max_file.text}")
						return int(min_file.text), int(max_file.text)
					else:
						print("ℹ️ Nincs letölthető naplófájl a pénztárgéphez.")
						return None, None

			except etree.XMLSyntaxError as e:
				print(f"XML elemzési hiba a státusz válaszban: {e}")
				
	return None, None


def parse_file_download_response(response: requests.Response):
	content_type = response.headers.get('Content-Type', '')
	boundary = extract_boundary(content_type, response.text)
	
	if not boundary:
		print("Hiba: Nem található 'boundary' a fájlletöltés válaszban.")
		return

	parts = response.content.split(f'--{boundary}'.encode('utf-8'))
	
	# Ebbe a szótárba gyűjtjük ki az XML-ből, hogy melyik Content-ID (cid) milyen fájlnévhez tartozik
	cid_to_filename_map = {}
	
	# 1. KÖR: XML feldolgozása a hozzárendelések (mapping) megtalálásához
	for part in parts:
		if not part.strip() or part.strip() == b'--': continue
		try:
			if b'\r\n\r\n' in part:
				header_bytes, content = part.split(b'\r\n\r\n', 1)
			else:
				continue
			headers = header_bytes.decode('utf-8').lower()
		except ValueError: continue

		if 'application/xop+xml' in headers or 'text/xml' in headers:
			try:
				xml_root = etree.fromstring(content.strip())
				ns = {
					'ns2': 'http://schemas.nav.gov.hu/NTCA/1.0/common',
					'ns3': 'http://schemas.nav.gov.hu/OPF/1.0/api',
					'xop': 'http://www.w3.org/2004/08/xop/include'
				}
				
				# Hibaellenőrzés
				func_code = xml_root.find('.//ns2:funcCode', namespaces=ns)
				if func_code is not None and func_code.text == "ERROR":
					err_msg = xml_root.find('.//ns2:message', namespaces=ns)
					print(f"❌ NAV HIBA a letöltés során: {err_msg.text if err_msg is not None else 'Ismeretlen'}")
					return

				# Mapping felépítése: cid -> cashRegisterFileName
				for file_node in xml_root.findall('.//ns3:cashRegisterFile', namespaces=ns):
					f_name_node = file_node.find('ns3:cashRegisterFileName', namespaces=ns)
					inc_node = file_node.find('.//xop:Include', namespaces=ns)
					
					if f_name_node is not None and inc_node is not None:
						href = inc_node.get('href')
						if href and href.startswith('cid:'):
							clean_cid = href[4:] # Eltávolítjuk a "cid:" előtagot
							
							# A .p7b kiterjesztés cseréje .zip-re
							raw_filename = f_name_node.text
							if raw_filename.lower().endswith('.p7b'):
								final_filename = raw_filename[:-4] + ".zip"
							else:
								final_filename = raw_filename + ".zip"
								
							cid_to_filename_map[clean_cid] = final_filename
							
			except etree.XMLSyntaxError: pass

	# 2. KÖR: Bináris ZIP fájlok lementése a megtalált fájlnevek alapján
	file_count = 0
	for part in parts:
		if not part.strip() or part.strip() == b'--': continue
		try:
			if b'\r\n\r\n' in part:
				header_bytes, content = part.split(b'\r\n\r\n', 1)
			else:
				continue
			headers = header_bytes.decode('utf-8').lower()
		except ValueError: continue

		if 'binary' in headers or 'application/octet-stream' in headers or 'application/zip' in headers:
			# Content-ID megkeresése a part fejlécében
			content_id = None
			for line in headers.split('\n'):
				if line.startswith('content-id:'):
					content_id = line.split(':', 1)[1].strip().strip('<>')
			
			# Fájlnév azonosítása a térkép alapján (vagy fallback uuid-ra, ha valamiért nem találná)
			filename = cid_to_filename_map.get(content_id, f"naplo_fallback_{str(uuid.uuid4().hex[:6])}.zip")
			
			# Záró sortörések lecsípése
			if content.endswith(b'\r\n'):
				content = content[:-2]

			# Fájl elmentése (A 'wb' automatikusan felülírja a már létezőt)
			filepath = os.path.join(TARGET_FOLDER, filename)
			
			with open(filepath, 'wb') as f:
				f.write(content)
				
			print(f"💾 Fájl mentve: {filepath} ({len(content)} bájt)")
			file_count += 1
			
	if file_count == 0:
		print("⚠️ A letöltés lefutott, de nem érkezett menthető naplófájl a válaszban.")


# --- FŐ PROGRAM ---
if __name__ == "__main__":
	print(f"\n[1/2] {CASHREGISTER_ID} PÉNZTÁRGÉP STÁTUSZ LEKÉRDEZÉSE...")

	req_id_status = f"RID_{uuid.uuid4().hex[:20].upper()}"
	ts_xml = get_utc_timestamp_str()
	ts_sig = get_signature_timestamp_str()
	
	pwd_h = create_password_hash(PASSWORD)
	req_sig_status = create_request_signature(req_id_status, ts_sig, SIGNATURE_KEY)

	xml_status = build_status_xml_request(req_id_status, ts_xml, pwd_h, req_sig_status, CASHREGISTER_ID)

	headers = {
		'Content-Type': 'application/soap+xml; charset=utf-8',
		'Accept': 'multipart/related, application/soap+xml, application/xml',
		'User-Agent': 'Arsuna-Downloader/1.0'
	}
	
	try:
		response_status = requests.post(STATUS_URL, data=xml_status.encode('utf-8'), headers=headers, timeout=30)
		
		if response_status.status_code == 200:
			min_sorszam, max_sorszam = parse_status_response(response_status)
			
			if min_sorszam is not None and max_sorszam is not None:
				print(f"\n[2/2] NAPLÓFÁJLOK LETÖLTÉSE ({min_sorszam} - {max_sorszam})...")
				
				req_id_file = f"RID_{uuid.uuid4().hex[:20].upper()}"
				ts_xml_file = get_utc_timestamp_str()
				ts_sig_file = get_signature_timestamp_str()
				
				req_sig_file = create_request_signature(req_id_file, ts_sig_file, SIGNATURE_KEY)
				
				xml_file = build_file_download_xml_request(
					req_id_file, ts_xml_file, pwd_h, req_sig_file, 
					CASHREGISTER_ID, min_sorszam, max_sorszam
				)
				
				response_file = requests.post(FILE_URL, data=xml_file.encode('utf-8'), headers=headers, timeout=60)
				
				if response_file.status_code == 200:
					parse_file_download_response(response_file)
				else:
					print(f"❌ HTTP Hiba a letöltésnél: {response_file.status_code}")
					print(response_file.text[:500])
					
		else:
			print(f"❌ HTTP Hiba a státusz lekérdezésnél: {response_status.status_code}")
			print(response_status.text[:500])

	except requests.exceptions.RequestException as e:
		print(f"Hálózati hiba történt: {e}")