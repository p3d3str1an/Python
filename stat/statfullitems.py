from google.cloud import bigquery
from google.oauth2 import service_account
from oauth2client.service_account import ServiceAccountCredentials
from auDAOlib import notifyover, readPROD, setup_logging
import logging
from credentials import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, GOOGLE_APPLICATION_CREDENTIALS_FILE

setup_logging(log_filename='fullitemstat.log',place=1)
credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_FILE)
client = bigquery.Client(credentials=credentials)
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")



# fullitemstat
sqlQuery5 = '''
				SELECT id, cikknev, sum(nettó) osszeg, sum(darab) as db, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum, datepart(dy,datum) ytd,
				case when vkód in ('WEB', 'WEBC', 'bolt', 'boltszla') then 'magánvásárló' else 'viszonteladó' end vevotipus 
				FROM AUAssist.dbo.sales 
				where ev>'2022' 
				and id not in ('1003', '1014', '1020', '1026', '1028', '1021')
				and cikktulajdonság not like '%állvány%'
				group by id, cikknev, vevőcsoport, vevőcsop2, vkód, ev, month(datum), datum
				'''
sales5 = readPROD(sqlQuery5)
logging.info('fullitemstat queried')

if sales5.empty:
	notifyover('fullitemstat', 'No data found for fullitemstat.')
	logging.warning("No data found for fullitemstat. Skipping upload.")
else:
	try:
		table_id = BIGQUERY_PROJECT_ID + '.' + BIGQUERY_DATASET_ID + f'.fullitemstat'
		job = client.load_table_from_dataframe(
			sales5, table_id, job_config=job_config
		)
		job.result(timeout=300)  # Wait for the job to complete.
		logging.info(f"Loaded {job.output_rows} rows into {table_id}.")
	except Exception as error:	
		notifyover('fullitemstat', repr(error))
		logging.error(f"Failed to load data into {table_id}: {error}")	
