#Vibe coded with Gemini
# A letöltött pénztárgépnapló fájlokból a kicsomagolja a p7b-t és kiemeli belőle az xml-t


import os
import zipfile
from asn1crypto import cms
from credentials import KOZOSPATH


# --- KONFIGURÁCIÓ ---
# A letöltő script által használt mappa, ahol a ZIP-ek vannak
SOURCE_FOLDER = KOZOSPATH+r"\PÉNZÜGY\BEOLVASÓK\Pénztárgép\zip"
# Ide fogja menteni a tiszta XML fájlokat
XML_OUTPUT_FOLDER = KOZOSPATH+r"\PÉNZÜGY\BEOLVASÓK\Pénztárgép"

def extract_xml_from_p7b(p7b_bytes: bytes) -> bytes:
	"""
	Kinyeri az XML tartalmat a P7B (CMS SignedData) állományból.
	Implementálja a hivatalos módszert és a minta alapú "kitúrást" is. - minta a renced42 féle java volt.
	https://github.com/nav-gov-hu/Online-Cash-Register-Logfile/issues/15#issuecomment-1290174525
	"""
	# --- 1. MÓDSZER: Hivatalos PKI / CMS parsing ---
	try:
		info = cms.ContentInfo.load(p7b_bytes)
		signed_data = info['content']
		encap_content_info = signed_data['encap_content_info']
		
		xml_content = encap_content_info['content'].native
		
		if xml_content and b'<?xml' in xml_content:
			return xml_content
			
	except Exception as e:
		print(f"  [!] Hivatalos CMS parsing nem sikerült, jöhet a B-terv...")

	# --- 2. MÓDSZER: A szolgáltató által javasolt "minta alapú kitúrás" (Fallback) ---
	try:
		begin_pattern = b'<?xml'
		end_pattern = b'WS>'
		
		start_idx = p7b_bytes.find(begin_pattern)
		if start_idx != -1:
			end_idx = p7b_bytes.rfind(end_pattern)
			if end_idx != -1 and end_idx > start_idx:
				return p7b_bytes[start_idx:end_idx + 3]
	except Exception as e:
		print(f"  [!] A minta alapú kitúrás is elhasalt: {e}")

	return None

def main():
	print("🚀 P7B Naplófájlok feldolgozása és XML kinyerése...")
	
	if not os.path.exists(SOURCE_FOLDER):
		print(f"Hiba: A mappa ({SOURCE_FOLDER}) nem létezik. Futtasd először a letöltő scriptet!")
		return

	# Létrehozzuk a kimeneti mappát, ha nem létezik
	os.makedirs(XML_OUTPUT_FOLDER, exist_ok=True)
	print(f"📁 Kinyert XML-ek célmappája: {os.path.abspath(XML_OUTPUT_FOLDER)}")

	processed_files = 0

	# Végigmegyünk a mappában lévő összes ZIP fájlon
	for filename in os.listdir(SOURCE_FOLDER):
		if filename.endswith(".zip"):
			filepath = os.path.join(SOURCE_FOLDER, filename)
			print(f"\nFeldolgozás: {filename}")
			
			try:
				# Kinyitjuk a ZIP-et a memóriában
				with zipfile.ZipFile(filepath, 'r') as zf:
					for inner_filename in zf.namelist():
						if inner_filename.lower().endswith('.p7b'):
							print(f"  -> {inner_filename} kibontása...")
							
							p7b_bytes = zf.read(inner_filename)
							xml_bytes = extract_xml_from_p7b(p7b_bytes)
							
							if xml_bytes:
								# ÚJ LOGIKA: A p7b fájl nevének kinyerése
								# (os.path.basename leszedi az esetleges ZIP-en belüli almappákat)
								p7b_basename = os.path.splitext(os.path.basename(inner_filename))[0]
								
								# Fájl elmentése az új mappába a p7b nevével
								xml_filename = f"{p7b_basename}.xml"
								xml_filepath = os.path.join(XML_OUTPUT_FOLDER, xml_filename)
								
								with open(xml_filepath, 'wb') as f:
									f.write(xml_bytes)
									
								processed_files += 1
								print(f"  ✅ XML sikeresen mentve: {xml_filename}")
							else:
								print("  ❌ Nem sikerült érvényes XML-t kinyerni a fájlból.")
								
			except Exception as e:
				print(f"Hiba a {filename} olvasásakor: {e}")

	print(f"\n🎉 KÉSZ! Összesen {processed_files} db XML fájl lett kimentve.")

if __name__ == "__main__":
	main()