from oauth2client.service_account import ServiceAccountCredentials
from google.cloud import bigquery
from google.oauth2 import service_account
from credentials import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, GOOGLE_APPLICATION_CREDENTIALS_FILE
from auDAOlib import notifyover, readPROD, readWEB, setup_logging
import logging

setup_logging(log_filename='stat.log',place=0)

credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_FILE)
client = bigquery.Client(credentials=credentials)
job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")


def bigquery_load(table, data):
	table_id = BIGQUERY_PROJECT_ID + '.' + BIGQUERY_DATASET_ID + f'.{table}'

	try:
		job= client.load_table_from_dataframe(
		data, table_id, job_config=job_config
	)
		job.result()  # Wait for the job to complete.
		logging.info(f"Loaded {job.output_rows} rows into {table_id}.")
	except Exception as error:
		notifyover('webstat',repr(error))
		logging.error(f"Failed to load data into {table_id}: {error}")

bigquery_load(table='webshop_data', )


# datapython
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', vnev, ev, month(datum) honap FROM AUAssist.dbo.sales where ev>='2021' group by vevőcsoport, vevőcsop2, vkód, vnev, ev, month(datum)"
sales = readPROD(sqlQuery)
print('datapython queried')
logging.info('datapython queried')

# fullstat
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum FROM AUAssist.dbo.sales where ev>='2021' group by vevőcsoport, vevőcsop2, vkód, ev, month(datum), datum"
sales2 = readPROD(sqlQuery)
print('fullstat queried')

# ytdstat
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum, datepart(dy,datum) ytd FROM AUAssist.dbo.sales where ev>='2021' and datepart(dy,datum)<=(select max(datepart(dy,datum)) from AUAssist.dbo.sales where ev=year(getdate())) group by vevőcsoport, vevőcsop2, vkód, ev, month(datum), datum"
sales3 = readPROD(sqlQuery)
print('ytdstat queried')

# webstat 
sqlQuery = r"SELECT o.order_id, from_unixtime(o.timestamp, '%Y%m%d') date,lpad(month(from_unixtime(o.timestamp)),2,0) honap,lpad(day(from_unixtime(o.timestamp)),2,0) nap,year(from_unixtime(o.timestamp)) ev, o.total, o.shipping_ids shipping, sd.description, case when o.shipping_ids in (12,1,13,11,6) then 'magánvásárló' when o.shipping_ids in (14,10,8,9) then 'viszonteladó' end csoport FROM cscart_orders o join cscart_statuses s on s.status=o.status and s.type='O' join cscart_status_descriptions sd on sd.status_id=s.status_id and sd.lang_code='hu' where from_unixtime(o.timestamp)>CURDATE()- INTERVAL 2 year and o.status in ('P', 'C', 'O', 'A', 'E', 'G', 'H')"
sales4 = readWEB(sqlQuery)
print('webstat queried') 
###


### kiszedve a harmadik sorból ez (ytd): and datepart(dy,datum)<=(select max(datepart(dy,datum)) from AUAssist.dbo.sales where ev=2021), mert a ytdstatot a sales3 query nézi 

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
#sales5 = readPROD(sqlQuery5)
print('fullitemstat queried')


try:
	worksheet2 = spreadsheet2.worksheet('fullstat')
	worksheet2.clear()
	worksheet2.update([sales2.columns.values.tolist()] + sales2.values.tolist())
	print('fullstat filled')
except Exception as error:
	notifyover('fullstat',repr(error))	 
try:
	worksheet = spreadsheet.worksheet('datapython')
	worksheet.clear()
	worksheet.update([sales.columns.values.tolist()] + sales.values.tolist())
	print('stat.datapython filled')
except Exception as error:
	notifyover('datapython',repr(error))
try:
	worksheet3 = spreadsheet.worksheet('ytdstat')
	worksheet3.clear()
	worksheet3.update([sales3.columns.values.tolist()] + sales3.values.tolist())
	print('stat.ytdstat filled')
except Exception as error:
	notifyover('ytdstat',repr(error))	 
try:
	worksheet4 = spreadsheet4.worksheet('web_sales')
	worksheet4.clear()
	worksheet4.update([sales4.columns.values.tolist()] + sales4.values.tolist())
	print('webstat filled')
except Exception as error:
	notifyover('sales4',repr(error))																																				 

try:
	# ez külön fájlban van, mert ritkábban frissül, mint a többi
#	worksheet5 = spreadsheet5.worksheet('data')
#	worksheet5.clear()
#	worksheet5.update([sales5.columns.values.tolist()] + sales5.values.tolist())
	print('fullitemstat.data filled')
except Exception as error:
	notifyover('fullitemstat',repr(error))

