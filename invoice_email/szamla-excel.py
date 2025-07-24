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
        T1.ItemCode [au-cikkszám],
        t1.dscription [cikknév],
        t1.SubCatNum [cikkszám], 
        T1.CodeBars [vonalkód], 
        cast(T1.Quantity as int) [db], 
        cast(T1.Price as money) [nettó ár]
    FROM OINV T0 
    INNER JOIN INV1 T1 ON T0.DocEntry = T1.DocEntry
    WHERE T0.DocNum = '{invoice_number}'
    """

    # Get data using readPROD
    invoice_df = readPROD(query)

    if invoice_df.empty:
        print(f"No data found for invoice number: {invoice_number}")
        return

    # Define the Excel file name
    excel_filename = f"{KOZOSPATH}\\SBO\\Attachments\\{invoice_number}_szamlatetelek.xlsx"

    # Export to Excel
    invoice_df.to_excel(excel_filename, index=False)
    print(f"Invoice data exported to {excel_filename}")

    # Send email with yagmail
    try:
        yag = yagmail.SMTP(user=ARSUNA_EMAIL_USER, password=ARSUNA_EMAIL_PASSWORD)
        subject = f"A {invoice_number} számla tételei"
        body = f"""
        	<h3>Tisztelt Címzett!</h3>
			<p></p>						
			<p>Köszönjük hogy minket választott!<br>Mellékelten küldjük a <strong>{invoice_number}</strong> számú számlájának tételeit excel formátumban.</p>
			<p></p>						
			<p>Ez egy automata üzenet, kérem ha észrevétele van, a web@arsuna.hu címen jelezze!</p>
			<p>Üdvözlettel,<br>
			Ars Una Studio<p>
			"""
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