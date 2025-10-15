# the additional Excel exporter are vibecoded with Gemini

import os
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from auDAOlib import readPROD as readSQL, notifyover, updatePROD as updateSQL, setup_logging # renamed for easier testing
from unidecode import unidecode
from credentials import ARSUNA_EMAIL_USER, ARSUNA_EMAIL_PASSWORD, KOZOSPATH
import pandas as pd
import logging

# Function to authenticate with Gmail
def authenticate_gmail(felhasznalo, jelszo):
	# Gmail authentication
	smtp_server = "smtp.gmail.com"
	port = 587  # For starttls
	sender_email = felhasznalo  # Enter your address
	password = jelszo # Enter your password
	try:
		context = ssl.create_default_context()
		server = smtplib.SMTP(smtp_server, port)
		server.starttls(context=context)
		server.login(sender_email, password)
		return server, ''
	except smtplib.SMTPException as e:
		return server, f"Hiba: {e}"


def send_gmail(server, felhasznalo, cimzett, text):
	sanitized_error=''
	try:
		server_response = server.sendmail(felhasznalo, cimzett, text)
		sanitized_error=server_response
	except smtplib.SMTPRecipientsRefused as e:
		sanitized_error = "All recipients were refused."
	except smtplib.SMTPSenderRefused as e:
		sanitized_error = f"Sender address refused: {e.smtp_code} - {e.smtp_error.decode()}"
	except smtplib.SMTPDataError as e:
		sanitized_error = f"SMTP data error: {e.smtp_code} - {e.smtp_error.decode()}"
	except smtplib.SMTPException as e:
		sanitized_error = "SMTP error occurred. Check server and credentials."
	except Exception as e:
		sanitized_error = "Unexpected error occurred during email sending."
	return sanitized_error

def export_invoice_to_excel(invoice_number):
	"""
	Retrieves invoice data, exports it to an Excel file

	Args:
		invoice_number (str): The invoice number to retrieve data for.
	"""

	# SQL query to get invoice data
	query = f"""
	SELECT 
		T1.ItemCode [au_cikkszám],
		t1.dscription [cikknév],
		t1.SubCatNum [partner_cikkszám], 
		T1.CodeBars [vonalkód], 
		T1.Quantity [db], 
		T1.Price [nettó ár],
		T1.LineTotal [összesen]
	FROM OINV T0 
	INNER JOIN INV1 T1 ON T0.DocEntry = T1.DocEntry
	WHERE T0.DocNum = '{invoice_number}'
	"""

	invoice_df = readSQL(query)

	if invoice_df.empty:
		logging.warning(f"No data found for invoice number: {invoice_number}")
		return
	# Convert price column to a numeric type so Excel formatting will work
	invoice_df['nettó ár'] = pd.to_numeric(invoice_df['nettó ár'], errors='coerce')

	excel_filename = f"{KOZOSPATH}\\SBO\\Attachments\\{invoice_number}_szamlatetelek.xlsx"

	# 1. Create an Excel writer object using the XlsxWriter engine.
	with pd.ExcelWriter(excel_filename, engine='xlsxwriter') as writer:
		invoice_df.to_excel(writer, sheet_name='SzámlaTételek', index=False)
		workbook  = writer.book
		worksheet = writer.sheets['SzámlaTételek']
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
			
			if col == 'nettó ár' or col == 'összesen':
				# Apply both width and currency format to the 'nettó ár' and 'össszesen' columns
				worksheet.set_column(idx, idx, max_len, currency_format)
			else:
				# Just apply the calculated width to other columns
				worksheet.set_column(idx, idx, max_len)
	
	logging.info(f"Invoice data exported to {excel_filename}")
	return excel_filename

def main():
	setup_logging(log_filename='szamlakuldo.log',place=1)
	felhasznalo = ARSUNA_EMAIL_USER
	jelszo = ARSUNA_EMAIL_PASSWORD
	#jelszo ='rossz'
	server, hiba = authenticate_gmail(felhasznalo, jelszo)
	if hiba: 
		notifyover('Email',hiba)
		logging.error(hiba)
		return
	exceltrue = """
			  '134011361','134011623','134011469','134011617','7100105'
			  """
	kuldendoQry = f'''
					select code, name, o.u_email email, i.CardName nev, iif(isnull(a.absentry,1)=1, null, concat(a.trgtPath,'\\',a.filename,'.pdf')) filename, 
					case when i.cardcode in ({exceltrue}) then 'Y' else 'N' end excel
					from [@EMAIL_OBJECTS] o
					join oinv i on i.docentry=o.U_docentry and o.U_objtype=13
					left join atc1 a on a.AbsEntry=i.AtcEntry and a.filename like concat('%',name,'%')
					where o.U_status='TT' and i.series not in (551,539, 540, 553)
					'''
	kuldendok = readSQL(kuldendoQry)
	updateQry = '''update [@email_objects] set u_status = :status, u_result = :result where code = :code'''

	if kuldendok.empty:
		logging.info("No invoices to send.")

	for index, row in kuldendok.iterrows():
		docnum = row['name']
		filepath = row['filename']
		email= row['email']
		nev = row['nev']
		code = row['code']
		excelfile = export_invoice_to_excel(docnum) if row['excel'] == 'Y' else None
		try:
			email_list = email.strip().split(',')
			msg = MIMEMultipart()
			msg['From'] = felhasznalo
			msg['To'] = ', '.join(email_list)
			msg['Subject'] = f"Ars Una számlája érkezett"
			msg['Reply-To'] ='web@arsuna.hu'
			body = MIMEText(f"""
			<h3>Kedves {nev}!</h3>
			<p></p>						
			<p>Köszönjük hogy minket választott!<br>Mellékelten küldjük a <strong>{docnum}</strong> számú számláját.</p>
			<p>A csatolmány PDF formátumú, megnyitásához segédprogram (pl. az ingyenes Adobe Reader) szükséges. Kérem nyomtassa ki és kezelje úgy, mint egy papíralapú számlát.</p>
			<p></p>						
			<p>Ez egy automata üzenet, kérem ha észrevétele van, a web@arsuna.hu címen jelezze!</p>
			<p>Üdvözlettel,<br>
			Ars Una Studio<p>
			""", _subtype='html')				
			msg.attach(body)
			with open(filepath, "rb") as attachment: 
				part = MIMEBase('application', 'octet-stream')
				part.set_payload(attachment.read())
				encoders.encode_base64(part)
				part.add_header('Content-Disposition', f'attachment; filename="{unidecode(os.path.basename(filepath))}"') 
				msg.attach(part)
			if excelfile:
				with open(excelfile, "rb") as attachment: 
					part = MIMEBase('application', 'octet-stream')
					part.set_payload(attachment.read())
					encoders.encode_base64(part)
					part.add_header('Content-Disposition', f'attachment; filename="{unidecode(os.path.basename(excelfile))}"') 
					msg.attach(part)
			text = msg.as_string()
			response=send_gmail(server, felhasznalo, email_list, text)
			logging.info(f"Email with invoice {docnum} data tried to send to {email_list}")
			if response: raise Exception(response)
			params={'status': 'S', 'result': 'sent', 'code': code}
		except Exception as e:					
			params = {'status': 'ER', 'result': str(e)[:190], 'code': code}
		finally:
			updateSQL(updateQry, params)
		
	server.quit()

if __name__ == "__main__":
	main()
