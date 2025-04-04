import os
import smtplib, ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from auDAOlib import readPROD as readSQL, notifyover, updatePROD as updateSQL
from unidecode import unidecode
from credentials import ARSUNA_EMAIL_USER, ARSUNA_EMAIL_PASSWORD

felhasznalo = ARSUNA_EMAIL_USER
jelszo = ARSUNA_EMAIL_PASSWORD
#jelszo ='rossz'

# Function to authenticate with Gmail
def authenticate_gmail():
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


def main():
	server, hiba = authenticate_gmail()
	if hiba: 
		notifyover('Email',hiba)
		return
	kuldendoQry = 	'''
					select code, name, o.u_email email, i.CardName nev, iif(isnull(a.absentry,1)=1, null, concat(a.trgtPath,'\\',a.filename,'.pdf')) filename
					from [@EMAIL_OBJECTS] o
					join oinv i on i.docentry=o.U_docentry and o.U_objtype=13
					left join atc1 a on a.AbsEntry=i.AtcEntry and a.filename like concat('%',name,'%')
					where o.U_status='TS' and i.series not in (551,539, 540, 553)
					'''
	kuldendok = readSQL(kuldendoQry)
	updateQry = '''update [@email_objects] set u_status = :status, u_result = :result where code = :code'''

	for index, row in kuldendok.iterrows():
		docnum = row['name']
		filepath = row['filename']
		email= row['email']
		nev = row['nev']
		code = row['code']
		try:
			file = unidecode(os.path.basename(filepath))
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
			<p>A csatolmány PDF formátumú, megnyitásához segédprogram (pl. az ingyenes Adobe Reader) szükséges.</p>
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
				part.add_header('Content-Disposition', f'attachment; filename="{file}"') 
				msg.attach(part)
			text = msg.as_string()
			response=send_gmail(server, felhasznalo, email_list, text)
			if response: raise Exception(response)
			params={'status': 'S', 'result': 'sent', 'code': code}
		except Exception as e:					
			params = {'status': 'ER', 'result': str(e)[:190], 'code': code}
		finally:
			updateSQL(updateQry, params)
		
	server.quit()

if __name__ == "__main__":
	main()
