import pandas as pd
from pushover import Client
import yagmail
from sqlalchemy import create_engine, text, URL
from credentials import DATABASES, PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN, YAGMAIL_USER, YAGMAIL_PASSWORD
import logging, sys


def DAO(qry, db, op):
	"""
	Data Access Object for handling database operations.

	Args:
		qry: The query or command to execute.
			- For 'read': An SQL query string.
			- For 'exec': A stored procedure name (string).
			- For 'upd': An SQL statement string, or a tuple of (sql_string, params_dict).
		db (str): The key for the database configuration in DATABASES.
		op (str): The operation to perform: 'read', 'exec', or 'upd'.
	"""
	if db not in DATABASES:
			print(f"Error: Database '{db}' not found in configurations.")
			return None

	db_config = DATABASES[db]
	is_mysql = db in ('ARSUNAHU', 'ARSUNAHUTESZT')

	if is_mysql:
		connection_url = URL.create(
			'mysql+mysqlconnector',
			username=db_config['username'],
			password=db_config['password'],
			host=db_config['host'],
			port=db_config['port'],
			database=db_config['database']
		)
	else:
		# SQL Server
		connection_string = (
			'DRIVER={SQL Server};SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s' % (
				db_config['server'], db_config['port'], db_config['database'],
				db_config['username'], db_config['password']
			)
		)
		connection_url = URL.create("mssql+pyodbc", query={"odbc_connect": connection_string})

	engine = create_engine(connection_url)

	try:
		if op == 'read':
			with engine.begin() as conn:
				df = pd.read_sql(qry, conn)
			return df

		elif op == 'exec':
			with engine.begin() as conn:
				if is_mysql:
					# Use raw connection for MySQL stored procedures
					raw_conn = conn.connection
					cursor = raw_conn.cursor()
					cursor.callproc(qry)
					cursor.close()
					raw_conn.commit()
				else:
					# SQL Server stored procedure call
					conn.execute(text(f"EXEC dbo.{qry}"))

		elif op == 'upd':
			# This block now correctly handles updates/inserts/deletes for both MySQL and SQL Server.
			sql, params = ("", {})
			try:
				# Unpack query and parameters if passed as a tuple
				if isinstance(qry, (list, tuple)) and len(qry) == 2:
					sql, params = qry
				else:
					# Assume a simple string query with no parameters
					sql, params = qry, {}
				with engine.begin() as conn:
					stmt = text(sql)
					conn.execute(stmt, params)
			except Exception as e:
					notifyover('SQL', f"Update error: {e}")
	except Exception as e:
		print(f"An error occurred in DAO function: {e}")
	finally:
		if 'engine' in locals():
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

def readWEBTESZT(query: str):
	"""
	SQL query futtatás az webes adatbázison -> dataframe
	"""
	dataFrame = DAO(query, 'ARSUNAHUTESZT','read')
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

def updateWEB(query: str, args: list):
	"""
	update az arsuna.hu adatbázison
	"""
	DAO([query, args],'ARSUNAHU','upd')

def updateWEBTESZT(query: str, args: list):
	"""
	update az arsuna.hu TESZT adatbázison
	"""
	DAO([query, args],'ARSUNAHUTESZT','upd')

def execASSIST(proc: str):
	"""
	Tárolt eljárás futtatás az assist adatbázison
	"""
	DAO(proc,'ASSIST','exec')

def execWEB(proc: str):
	"""
	Tárolt eljárás futtatás az webes adatbázison
	"""
	DAO(proc,'ARSUNAHU','exec')

def execWEBTESZT(proc: str):
	"""
	Tárolt eljárás futtatás az webes adatbázison
	"""
	DAO(proc,'ARSUNAHUTESZT','exec')

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
	except Exception as e:
		print(f'Pushover hiba: {e}')

def notifymail(addr='it@arsuna.hu', subj='Figyelmeztetés', mess='Kitöltetlen üzenettartalom'):
	"""
	Értesítés emailban
	"""
	try:
		yag = yagmail.SMTP(user=YAGMAIL_USER, password=YAGMAIL_PASSWORD)
		yag.send(to=addr, subject=subj, contents=mess)
	except:
		print('yagmail hiba')


def setup_logging(log_filename='app.log', level=logging.INFO, place=2): 
	"""
	Configures the root logger to log to a file and the console.
	This is an all-in-one setup function.
	place = 0 for file, 1 for console, 2 for both
	"""
	# Get the root logger
	logger = logging.getLogger()
	logger.setLevel(level)

	# Prevent duplicate handlers by clearing any existing ones
	if logger.hasHandlers():
		logger.handlers.clear()

	# Create the shared formatter
	formatter = logging.Formatter(
		'%(asctime)s - %(levelname)s - %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)

	if place == 0 or place == 2:
		# Create and add the file handler
		file_handler = logging.FileHandler(log_filename)
		file_handler.setFormatter(formatter)
		logger.addHandler(file_handler)

	if place == 1 or place == 2:
		# Create and add the console handler
		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(formatter)
		logger.addHandler(console_handler)
