# Invoice Email Exporter vibecoded with Gemini

import pandas as pd
import yagmail
from auDAOlib import readPROD
from credentials import ARSUNA_EMAIL_USER, ARSUNA_EMAIL_PASSWORD, KOZOSPATH

def export_invoice_to_excel_and_email(invoice_number, recipient_email):
    """
    Retrieves invoice data, exports it to an Excel file, and sends it via email.

    Args:
        invoice_number (str): The invoice number to retrieve data for.
        recipient_email (str): The email address to send the Excel file to.
    """

    # SQL query to get invoice data
    query = f"""
	SELECT 
        T1.ItemCode [au_cikkszám],
        t1.dscription [cikknév],
        t1.SubCatNum [partner_cikkszám], 
        T1.CodeBars [vonalkód], 
        T1.Quantity [db], 
        T1.Price [nettó ár]
    FROM OINV T0 
    INNER JOIN INV1 T1 ON T0.DocEntry = T1.DocEntry
    WHERE T0.DocNum = '{invoice_number}'
    """

    # Get data using readPROD
    invoice_df = readPROD(query)

    if invoice_df.empty:
        print(f"No data found for invoice number: {invoice_number}")
        return
	# Convert price column to a numeric type so Excel formatting will work
    invoice_df['nettó ár'] = pd.to_numeric(invoice_df['nettó ár'], errors='coerce')

    # Define the Excel file name
    excel_filename = f"{KOZOSPATH}\\SBO\\Attachments\\{invoice_number}_szamlatetelek.xlsx"

    # 1. Create an Excel writer object using the XlsxWriter engine.
    with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
        # 2. Write the dataframe to a sheet
        invoice_df.to_excel(writer, sheet_name='SzámlaTételek', index=False)

        # 3. Get the xlsxwriter workbook and worksheet objects.
        workbook  = writer.book
        worksheet = writer.sheets['SzámlaTételek']

        # 4. Create a currency format object. Using Forint (Ft) based on your column names.
        currency_format = workbook.add_format({'num_format': '#,##0 "Ft"'})

        # 5. Autofit columns and apply currency format to the price column.
        # Iterate through each column and set the width to the max length of the
        # data in that column, plus a little extra space.
        for idx, col in enumerate(invoice_df):
            series = invoice_df[col]
            # Find the maximum length of the header or the data in the column
            max_len = max(
                series.astype(str).map(len).max(),  # Length of longest data cell
                len(str(series.name))  # Length of the column header
            ) + 2  # Add a little padding
            
            # The column name for price is '[nettó ár]' from your SQL query
            if col == 'nettó ár':
                # Apply both width and currency format to the 'nettó ár' column (F)
                worksheet.set_column(idx, idx, max_len, currency_format)
            else:
                # Just apply the calculated width to other columns
                worksheet.set_column(idx, idx, max_len)

    # --- MODIFICATION END ---
    
    print(f"Invoice data exported to {excel_filename}")

    # Send email with yagmail
    try:
        yag = yagmail.SMTP(user=ARSUNA_EMAIL_USER, password=ARSUNA_EMAIL_PASSWORD)
        subject = f"A {invoice_number} számla tételei"
        body = f"""<h3>Tisztelt Címzett!</h3><p>Köszönjük hogy minket választott!<br>Mellékelten küldjük a <strong>{invoice_number}</strong> számú számlájának tételeit excel formátumban.</p><p>Ez egy automata üzenet, kérem ha észrevétele van, a web@arsuna.hu címen jelezze!</p><p>Üdvözlettel,<br>Ars Una Studio<p>"""
        yag.send(
            to=recipient_email,
            subject=subject,
            contents=body,
            attachments=excel_filename
        )
        print(f"Email with invoice data sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    # Example usage:
    # export_invoice_to_excel_and_email("2024000123", "test@example.com")
    export_invoice_to_excel_and_email("4012039", "it@arsuna.hu")
    pass