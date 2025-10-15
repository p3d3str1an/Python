import hashlib
import uuid
import datetime
import pytz
import requests
from lxml import etree
import ssl
import zipfile
import os
import csv
from requests.adapters import HTTPAdapter
from urllib3 import PoolManager
from asn1crypto import cms

from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER, CASHREGISTER_ID

# ===== Konfiguráció =====
ENV = "test"  # "test" vagy "prod"

if ENV== "test":
    NAV_USERNAME = "yefx1r11u2ihzz3"
    NAV_PASSWORD = "5S9&V&Y^k^wFDrRc"
    NAV_SIGNATURE_KEY = "61-92aa-c4d31a310c9352X8L6WQUHZ5"

URLS = {
    "test": {
        "status": "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus",
        "file":   "https://api-test-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"
    },
    "prod": {
        "status": "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus",
        "file":   "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterFile"
    }
}

XSD_PATH = "V2_AEEnaplo_6.6.5.xsd"

# ===== TLS1.2 adapter =====
class TLS12Adapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_version'] = ssl.PROTOCOL_TLSv1_2
        return super().init_poolmanager(*args, **kwargs)

# ===== Hash segédfüggvények =====
def sha512_upper(text):
    return hashlib.sha512(text.encode("utf-8")).hexdigest().upper()

def sha3_512_upper(text):
    return hashlib.sha3_512(text.encode("utf-8")).hexdigest().upper()

def utc_timestamp():
    return datetime.datetime.now(pytz.UTC).strftime("%Y%m%d%H%M%S")

def build_request_signature(request_id, timestamp):
    to_hash = f"{request_id}{timestamp}{NAV_SIGNATURE_KEY}"
    return sha3_512_upper(to_hash)

# ===== SOAP XML-ek =====
def build_status_request():
    request_id = str(uuid.uuid4())[:30]
    ts = utc_timestamp()
    password_hash = sha512_upper(NAV_PASSWORD)
    request_sig = build_request_signature(request_id, ts)

    return f"""
    <soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope"
                      xmlns:opf="http://schemas.nav.gov.hu/OPF/1.0/api""
                      xmlns:com="http://schemas.nav.gov.hu/NTCA/1.0/common">
        <soapenv:Header/>
        <soapenv:Body>
            <opf:QueryCashRegisterStatusRequest>
                <com:header>
                    <com:requestId>{request_id}</com:requestId>
                    <com:timestamp>{ts}</com:timestamp>
                    <com:requestVersion>1.0</com:requestVersion>
                </com:header>
                <com:user>
                    <com:login>{NAV_USERNAME}</com:login>
                    <com:passwordHash cryptoType="SHA-512">{password_hash}</com:passwordHash>
                    <com:taxNumber>{NAV_TAX_NUMBER}</com:taxNumber>
                    <com:requestSignature cryptoType="SHA3-512">{request_sig}</com:requestSignature>
                </com:user>
                <com:software>
                    <com:softwareId>HU10772335AU-AU-R002</com:softwareId>
                    <com:softwareName>ARSUNA receipts downloader chatgpt</com:softwareName>
                    <com:softwareOperation>LOCAL_SOFTWARE</com:softwareOperation>
                    <com:softwareMainVersion>1.0</com:softwareMainVersion>
                    <com:softwareDevName>Kovács Krisztián - ChatGPT</com:softwareDevName>
                    <com:softwareDevContact>it@arsuna.hu</com:softwareDevContact>
                    <com:softwareDevCountryCode>HU</com:softwareDevCountryCode>
                </com:software>
                <com:APNumberList>
                    <com:APNumber>{CASHREGISTER_ID}</com:APNumber>
                </com:APNumberList>
            </opf:QueryCashRegisterStatusRequest>
        </soapenv:Body>
    </soapenv:Envelope>
    """

def build_file_request(file_number):
    request_id = str(uuid.uuid4())[:30]
    ts = utc_timestamp()
    password_hash = sha512_upper(NAV_PASSWORD)
    request_sig = build_request_signature(request_id, ts)

    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope"
                      xmlns:opf="http://schemas.nav.gov.hu/OPG/2021/07/QueryCashRegisterFile">
        <soapenv:Header/>
        <soapenv:Body>
            <com:QueryCashRegisterFileDataRequest>
                <com:header>
                    <com:requestId>{request_id}</com:requestId>
                    <com:timestamp>{ts}</com:timestamp>
                    <com:requestVersion>1.0</com:requestVersion>
                </com:header>
                <com:user>
                    <com:login>{NAV_USERNAME}</com:login>
                    <com:passwordHash cryptoType="SHA-512">{password_hash}</com:passwordHash>
                    <com:taxNumber>{NAV_TAX_NUMBER}</com:taxNumber>
                    <com:requestSignature cryptoType="SHA3-512">{request_sig}</com:requestSignature>
                </com:user>
                <com:software>
                    <com:softwareId>HU12345678NAVTESTSW01</com:softwareId>
                    <com:softwareName>OPF Downloader</com:softwareName>
                    <com:softwareOperation>LOCAL_SOFTWARE</com:softwareOperation>
                    <com:softwareMainVersion>1.0</com:softwareMainVersion>
                    <com:softwareDevName>Fejlesztő Kft.</com:softwareDevName>
                    <com:softwareDevContact>fejleszto@example.com</com:softwareDevContact>
                    <com:softwareDevCountryCode>HU</com:softwareDevCountryCode>
                </com:software>
                <com:APNumber>{CASHREGISTER_ID}</com:APNumber>
                <com:FileNumberStart>{file_number}</com:FileNumberStart>
            </com:QueryCashRegisterFileDataRequest>
        </soapenv:Body>
    </soapenv:Envelope>
    """

# ===== NAV válasz feldolgozás =====
def check_for_nav_error(xml_content):
    try:
        xml = etree.fromstring(xml_content)
    except etree.XMLSyntaxError:
        return
    ns = {"opf": "http://schemas.nav.gov.hu/OPG/2021/07/QueryCashRegisterFile"}
    func_code = xml.xpath("//com:funcCode/text()", namespaces=ns)
    if func_code and func_code[0] == "ERROR":
        error_code = xml.xpath("//com:errorCode/text()", namespaces=ns)
        message = xml.xpath("//com:message/text()", namespaces=ns)
        raise RuntimeError(f"NAV hiba: {error_code[0] if error_code else 'N/A'} - {message[0] if message else 'Nincs üzenet'}")

# ===== PKCS#7 → XML =====
def extract_p7b_to_xml(p7b_path, output_xml_path):
    with open(p7b_path, "rb") as f:
        data = f.read()
    content_info = cms.ContentInfo.load(data)
    signed_data = content_info['content']
    for ci in signed_data['encap_content_info']['content']:
        xml_bytes = bytes(ci)
        with open(output_xml_path, "wb") as out_f:
            out_f.write(xml_bytes)
    return output_xml_path

# ===== XSD validáció =====
def validate_xml_with_xsd(xml_path, xsd_path):
    schema_doc = etree.parse(xsd_path)
    schema = etree.XMLSchema(schema_doc)
    xml_doc = etree.parse(xml_path)
    schema.assertValid(xml_doc)
    return xml_doc

# ===== NYT → CSV =====
def extract_receipts_to_csv(xml_doc, csv_path):
    root = xml_doc.getroot()
    rows = []
    for nyt in root.findall(".//NYT"):
        nsz = nyt.findtext("NSZ", "").strip()
        itl = nyt.findtext("ITL", "").strip()
        total = nyt.findtext("SUM", "").strip()
        rows.append([nsz, itl, total])

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerow(["Nyugtaszám", "Időbélyeg", "Összeg"])
        writer.writerows(rows)
    print(f"Nyugták CSV mentve: {csv_path}")

# ===== Kommunikáció =====
def get_last_file_number(session):
    xml_req = build_status_request()
    headers = {"Content-Type": "application/soap+xml; charset=UTF-8", "Accept": "application/soap+xml"}
    resp = session.post(URLS[ENV]["status"], data=xml_req, headers=headers)
    resp.raise_for_status()
    check_for_nav_error(resp.content)
    xml = etree.fromstring(resp.content)
    max_file = xml.xpath("//com:maxAvailableFileNumber", namespaces={"opf": "http://schemas.nav.gov.hu/OPG/2021/07/QueryCashRegisterFile"})
    if not max_file:
        raise ValueError("Nem található elérhető naplófájl.")
    return max_file[0].text

def download_and_process_file(session, file_number):
    xml_req = build_file_request(file_number)
    headers = {"Content-Type": "application/soap+xml; charset=UTF-8", "Accept": "application/soap+xml"}
    with session.post(URLS[ENV]["file"], data=xml_req, hstream=True) as r:
        r.raise_for_status()
        content_start = r.raw.read(200)
        if b"<?xml" in content_start:
            check_for_nav_error(content_start + r.raw.read())
            return
        else:
            zip_filename = f"log_{file_number}.zip"
            with open(zip_filename, "wb") as f:
                f.write(content_start)
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"ZIP mentve: {zip_filename}")

            with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
                zip_ref.extractall(os.getcwd())
            print(f"Kicsomagolva: {os.getcwd()}")

            for file in os.listdir(os.getcwd()):
                if file.lower().endswith(".p7b"):
                    p7b_path = os.path.join(os.getcwd(), file)
                    xml_path = os.path.splitext(p7b_path)[0] + ".xml"
                    extract_p7b_to_xml(p7b_path, xml_path)
                    xml_doc = validate_xml_with_xsd(xml_path, XSD_PATH)
                    extract_receipts_to_csv(xml_doc, "nyugtak.csv")

if __name__ == "__main__":
    session = requests.Session()
    session.mount("https://", TLS12Adapter())
    try:
        last_file_num = get_last_file_number(session)
        print(f"Utolsó elérhető naplófájl sorszáma: {last_file_num}")
        download_and_process_file(session, last_file_num)
    except Exception as e:
        print("Hiba történt:", e)
