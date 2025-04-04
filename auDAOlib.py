import pandas as pd
from pushover import Client
import yagmail
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from credentials import DATABASES, PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, YAGMAIL_USER, YAGMAIL_PASSWORD

def DAO(qry,db,op):
	if db in DATABASES:
		db_config = DATABASES[db]
		if db == 'ARSUNAHU':
			connection_url = URL.create('mysql+mysqlconnector', 
				username=db_config['username'], password=db_config['password'], host=db_config['host'], port=db_config['port'], database=db_config['database'])
		else:
			connection_string = 'DRIVER={SQL Server};SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s' % (
				db_config['server'], db_config['port'], db_config['database'], db_config['username'], db_config['password']
			)
			connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})
		
		engine = create_engine(connection_url)
		if op == 'read':
			with engine.begin() as conn:
				df = pd.read_sql(qry, conn)
			engine.dispose()
			return df
		elif op == 'exec':
			with engine.begin() as conn:
				conn.execute(text('execute dbo.' + qry))
			engine.dispose()
		elif op == 'upd':
			with engine.begin() as conn:
				try:
					stat = text(qry[0])
					conn.execute(stat, qry[1])
					conn.commit()
				except Exception as e:
					notifyover('SQL', f"Update error: {e}")
			engine.dispose()


def readPROD(query: str):
	"""
	SQL query futtatás az éles adatbázison -> dataframe
	"""
	dataFrame = DAO(query, 'PROD','read')
	return dataFrame
	
def readASSIST(query: str):
	"""
	SQL query futtatás az assist adatbázison -> dataframe
	"""
	dataFrame = DAO(query, 'ASSIST','read')
	return dataFrame

def readTESZT(query: str):
	"""
	SQL query futtatás az éles adatbázison -> dataframe
	"""
	dataFrame = DAO(query, 'TESZT','read')
	return dataFrame

def readWEB(query: str):
	"""
	SQL query futtatás az webes adatbázison -> dataframe
	"""
	dataFrame = DAO(query, 'ARSUNAHU','read')
	return dataFrame

def updatePROD(query: str, args: list):
	"""
	update a PROD adatbázison
	"""
	DAO([query, args],'PROD','upd')

def updateTESZT(query: str, args: list):
	"""
	update a TESZT adatbázison
	"""
	DAO([query, args],'TESZT','upd')

def execASSIST(proc: str):
	"""
	Tárolt eljárás futtatás az assist adatbázison
	"""
	DAO(proc,'ASSIST','exec')

def notify(mess: str):
	"""
	Értesítés küldése a telefonomra
	"""
	try:
		print('deprecated, válts notifyoverre!')
	except:
		print('Pushbullet hiba')

def notifyfrom(source, mess):
	"""
	Értesítés küldése a telefonomra, megadható hogy honnan
	"""
	try:
		print('deprecated, válts notifyoverre!')
	except:
		print('Pushbullet hiba')

def notifyover(source, mess):
	"""
	Értesítés az OP9pro-ra, pushoverrel, forrásmegadással
	"""
	try:
		pushclient = Client(PUSHOVER_USER_KEY, api_token=PUSHOVER_API_TOKEN)
		pushclient.send_message(mess, title=source)
	except:
		print('Pushover hiba')

def notifymail(addr='it@arsuna.hu', subj='Figyelmeztetés', mess='Kitöltetlen üzenettartalom'):
	"""
	Értesítés emailban
	"""
	try:
		yag = yagmail.SMTP(user=YAGMAIL_USER, password=YAGMAIL_PASSWORD)
		yag.send(to=addr, subject=subj, contents=mess)
	except:
		print('yagmail hiba')
