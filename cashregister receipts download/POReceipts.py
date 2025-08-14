# fully vibe coded with Gemini

import requests
import hashlib
import uuid
from datetime import datetime, timezone
from lxml import etree
import os
from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER, CASHREGISTER_ID

# --- API KONFIGURÁCIÓ ---
# Alapértelmezetten a teszt környezet van beállítva.
# Éles használathoz cseréld ki az URL-t az éles végpontra.
API_URL = "https://api-test.onlineszamla.nav.gov.hu/ptrfile/query"

# A kliens szoftver adatai, ezeket tetszőlegesen módosíthatod.
SOFTWARE_ID = "HU10772335AU-00003"
SOFTWARE_NAME = "ARSUNA receipts downloader"
SOFTWARE_VERSION = "1.0"
SOFTWARE_DEV_NAME = "Kovács Krisztián - Gemini 2.5 pro"
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
    A jelszót először nagybetűssé kell alakítani.
    """
    sha512 = hashlib.sha512()
    sha512.update(password.upper().encode('utf-8'))
    return sha512.hexdigest().upper()

def create_request_signature(request_id: str, timestamp_str: str, signing_key: str) -> str:
    """
    Létrehozza a kérés aláírását (requestSignature) a dokumentáció szerint (SHA3-512).
    A requestId, a speciális formátumú timestamp és az aláírókulcs összefűzéséből képződik. [cite: 93]
    """
    concatenated_string = f"{request_id}{timestamp_str}{signing_key}"
    sha3_512 = hashlib.sha3_512()
    sha3_512.update(concatenated_string.encode('utf-8'))
    return sha3_512.hexdigest().upper()

def build_xml_request(request_id: str, timestamp_utc: str, password_hash: str, request_signature: str) -> str:
    """
    Felépíti a SOAP XML kérést a megadott adatokból.
    """
    # Névterek definiálása
    ns = {
        "common": "http://schemas.nav.gov.hu/NTCA/1.0/common",
        "api": "http://schemas.nav.gov.hu/OSA/3.0/api",
        "base": "http://schemas.nav.gov.hu/OPF/1.0/cashregister"
    }

    # XML struktúra felépítése az lxml segítségével
    root = etree.Element("{http://schemas.nav.gov.hu/OPF/1.0/cashregister}QueryCashRegisterFileRequest", nsmap=ns)

    # Header
    header = etree.SubElement(root, "{http://schemas.nav.gov.hu/NTCA/1.0/common}header")
    etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestId").text = request_id
    etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}timestamp").text = timestamp_utc
    etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestVersion").text = "1.0"
    etree.SubElement(header, "{http://schemas.nav.gov.hu/NTCA/1.0/common}headerVersion").text = "1.0"

    # User
    user = etree.SubElement(root, "{http://schemas.nav.gov.hu/NTCA/1.0/common}user")
    etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}login").text = NAV_USERNAME
    
    pwd_hash_element = etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}passwordHash", cryptoType="SHA-512")
    pwd_hash_element.text = password_hash
    
    etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}taxNumber").text = NAV_TAX_NUMBER
    
    req_sig_element = etree.SubElement(user, "{http://schemas.nav.gov.hu/NTCA/1.0/common}requestSignature", cryptoType="SHA3-512")
    req_sig_element.text = request_signature

    # Software
    software = etree.SubElement(root, "{http://schemas.nav.gov.hu/OSA/3.0/api}software")
    etree.SubElement(software, "softwareId").text = SOFTWARE_ID
    etree.SubElement(software, "softwareName").text = SOFTWARE_NAME
    etree.SubElement(software, "softwareOperation").text = "LOCAL_SOFTWARE"
    etree.SubElement(software, "softwareMainVersion").text = SOFTWARE_VERSION
    etree.SubElement(software, "softwareDevName").text = SOFTWARE_DEV_NAME
    etree.SubElement(software, "softwareDevContact").text = SOFTWARE_DEV_CONTACT

    # Lekérdezés specifikus adatai
    # FIGYELEM: Itt kell megadni a pénztárgép AP számát és a kívánt napló sorszámtartományát!
    file_query_params = etree.SubElement(root, "{http://schemas.nav.gov.hu/OPF/1.0/cashregister}cashRegisterFileQuery")
    etree.SubElement(file_query_params, "cashRegisterId").text = CASHREGISTER_ID # <- CSERÉLD KI A PÉNZTÁRGÉP AZONOSÍTÓJÁRA
    etree.SubElement(file_query_params, "fromNumber").text = "1" # <- CSERÉLD KI A KEZDŐ SORSZÁMRA
    etree.SubElement(file_query_params, "toNumber").text = "1"   # <- CSERÉLD KI A ZÁRÓ SORSZÁMRA

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding='UTF-8').decode('utf-8')

def parse_mtom_response(response: requests.Response):
    """Feldolgozza a többrészes MTOM választ."""
    if 'multipart/related' not in response.headers.get('Content-Type', ''):
        print("Hiba: A válasz nem a várt multipart/related formátumú.")
        print("Válasz tartalma:")
        print(response.text)
        return

    # A requests nem kezeli natívan a multipart válaszokat, manuálisan kell feldolgozni
    # A határoló (boundary) a Content-Type headerből nyerhető ki
    content_type_parts = response.headers['Content-Type'].split(';')
    boundary = None
    for part in content_type_parts:
        if 'boundary=' in part:
            boundary = part.strip().split('=')[1].strip('"')
            break
            
    if not boundary:
        print("Hiba: Nem található a 'boundary' a Content-Type headerben.")
        return

    parts = response.content.split(f'--{boundary}'.encode('utf-8'))
    
    for part in parts:
        if not part.strip():
            continue
            
        # A part-ok fejléceit és tartalmát szétválasztjuk
        try:
            header_bytes, content = part.split(b'\r\n\r\n', 1)
            headers = header_bytes.decode('utf-8')
        except ValueError:
            continue

        # XML rész feldolgozása
        if 'application/xop+xml' in headers:
            print("--- XML Válasz Feldolgozása ---")
            xml_response_root = etree.fromstring(content)
            # Névtér a könnyebb kereséshez
            ns = {'base': 'http://schemas.nav.gov.hu/OPF/1.0/cashregister'}
            
            # Eredmény kód kiolvasása
            result_node = xml_response_root.find('.//base:result', namespaces=ns)
            if result_node is not None:
                func_code = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}funcCode').text
                print(f"Funkció kód: {func_code}")
                if func_code == "ERROR":
                    error_code = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}errorCode').text
                    message = result_node.find('{http://schemas.nav.gov.hu/NTCA/1.0/common}message').text
                    print(f"Hibakód: {error_code}")
                    print(f"Üzenet: {message}")
            else:
                 print("Nem található 'result' elem a válaszban.")

        # Bináris melléklet (naplófájl) feldolgozása
        if 'Content-Transfer-Encoding: binary' in headers:
            content_id_header = next((h for h in headers.split('\r\n') if h.lower().startswith('content-id:')), None)
            if content_id_header:
                content_id = content_id_header.split(':', 1)[1].strip().strip('<>')
                file_name = f"naplo_{content_id}.zip"
                print(f"\n--- Bináris Fájl Mentése ---")
                print(f"Talált naplófájl (Content-ID: {content_id}), mentés '{file_name}' néven...")
                with open(file_name, 'wb') as f:
                    f.write(content.strip(b'\r\n--'))
                print(f"'{file_name}' sikeresen mentve. Méret: {os.path.getsize(file_name)} bájt.")


# --- FŐ PROGRAM ---
if __name__ == "__main__":
    print("NAV naplóállomány lekérdező script indul...")

    # 1. Kérés egyedi azonosító generálása
    request_id = f"RID_{str(uuid.uuid4()).upper()}"
    print(f"Request ID: {request_id}")

    # 2. Időbélyegek generálása
    timestamp_for_xml = get_utc_timestamp_str()
    timestamp_for_sig = get_signature_timestamp_str()
    
    # 3. Hashek kiszámítása
    password_h = create_password_hash(NAV_PASSWORD)
    request_sig = create_request_signature(request_id, timestamp_for_sig, NAV_SIGNATURE_KEY)

    # 4. XML kérés összeállítása
    xml_payload = build_xml_request(request_id, timestamp_for_xml, password_h, request_sig)
    
    print("\n--- Elküldendő XML Kérés ---")
    print(xml_payload)
    print("--------------------------\n")

    # 5. HTTP kérés elküldése
    headers = {
        'Content-Type': 'application/xml; charset=utf-8',
        'Accept': 'application/xml'
    }
    
    try:
        print(f"Kérés küldése a(z) {API_URL} végpontra...")
        response = requests.post(API_URL, data=xml_payload.encode('utf-8'), headers=headers, timeout=30)
        
        print(f"Válasz érkezett. HTTP státuszkód: {response.status_code}")
        
        # 6. Válasz feldolgozása
        if response.status_code == 200:
            parse_mtom_response(response)
        else:
            print("Hiba történt a kérés során:")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"Hálózati hiba történt: {e}")