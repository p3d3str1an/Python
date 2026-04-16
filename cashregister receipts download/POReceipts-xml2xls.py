import os
import re
import pandas as pd
import xml.etree.ElementTree as ET

# --- KONFIGURÁCIÓ ---
SOURCE_FOLDER = r"\\nas\Kozos\PÉNZÜGY\BEOLVASÓK\Pénztárgép"
EXCEL_OUTPUT = r"\\nas\Kozos\PÉNZÜGY\BEOLVASÓK\Pénztárgép\nyugtak_kivonata.xlsx"

def extract_nyn_data(xml_string: str, source_filename: str) -> list:
    """
    Kikeresi a <NYN> blokkokat a nyers XML szövegből,
    és kinyeri belőlük a kért mezőket.
    """
    data_rows = []
    
    nyn_blocks = re.findall(r'<NYN>.*?</NYN>', xml_string, re.DOTALL)
    
    for block in nyn_blocks:
        try:
            root = ET.fromstring(block)
            
            # Tételösszegek matematikai szummázása
            su_elements = root.findall('.//SU')
            su_total = 0
            for el in su_elements:
                if el.text:
                    try:
                        su_total += int(float(el.text))
                    except ValueError:
                        pass
            
            # Adatsor összeállítása
            row = {
                'Forrás Fájl': source_filename,
                'Dátum (DTS)': root.findtext('.//DTS'),
                'Nyugtaszám (NSZ)': root.findtext('.//NSZ'),
                'Tételek Összege (SU)': su_total,
                'Készpénz (FE1)': root.findtext('.//FE1'),
                'Bankkártya (FE2)': root.findtext('.//FE2'),
                'Egyéb fizetés (FEN)': root.findtext('.//FEN'),
                'Kerekítés (RND)': root.findtext('.//RND'),
                'NAV Ellenőrző Kód (NAV)': root.findtext('.//NAV')
            }
            data_rows.append(row)
            
        except ET.ParseError as e:
            print(f"  [!] Hiba egy NYN blokk feldolgozásakor a {source_filename} fájlban: {e}")
            
    return data_rows

def main():
    print("🚀 NYN (Nyugta) blokkok feldolgozása és Excel export indítása...")
    
    if not os.path.exists(SOURCE_FOLDER):
        print(f"Hiba: A mappa ({SOURCE_FOLDER}) nem létezik.")
        return

    all_receipts = []

    for filename in os.listdir(SOURCE_FOLDER):
        if filename.endswith(".xml"):
            filepath = os.path.join(SOURCE_FOLDER, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                receipts = extract_nyn_data(content, filename)
                if receipts:
                    all_receipts.extend(receipts)
                    print(f"  ✅ {filename}: {len(receipts)} db nyugta.")
            except Exception as e:
                print(f"Hiba a {filename} olvasásakor: {e}")

    if not all_receipts:
        print("\n⚠️ Nincs feldolgozható adat.")
        return

    # Pandas DataFrame létrehozása
    df = pd.DataFrame(all_receipts)

    # --- DÁTUM KONVERTÁLÁSA ---
    # Átalakítjuk valódi dátum típussá. Az 'utc=True' segít az időzónák kezelésében.
    df['Dátum (DTS)'] = pd.to_datetime(df['Dátum (DTS)'], errors='coerce')
    
    # Eltávolítjuk az időzóna információt, hogy az Excel natívan kezelhesse dátumként
    df['Dátum (DTS)'] = df['Dátum (DTS)'].dt.tz_localize(None)

    # Számokká konvertálás
    numeric_columns = ['Tételek Összege (SU)', 'Készpénz (FE1)', 'Bankkártya (FE2)', 'Egyéb fizetés (FEN)', 'Kerekítés (RND)']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Excel mentése
    # A dátumot az Excel automatikusan a rendszerednek megfelelő hosszú formátumban fogja mutatni.
    df.to_excel(EXCEL_OUTPUT, index=False, engine='openpyxl')
    
    print(f"🎉 KÉSZ! Mentve: {os.path.abspath(EXCEL_OUTPUT)}")

if __name__ == "__main__":
    main()