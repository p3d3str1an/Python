from google.cloud import bigquery
from google.oauth2 import service_account
from auDAOlib import notifyover, readWEB
from credentials import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, GOOGLE_APPLICATION_CREDENTIALS_FILE

# webstat 
sqlQuery = r"SELECT o.order_id, from_unixtime(o.timestamp, '%Y%m%d') date,lpad(month(from_unixtime(o.timestamp)),2,0) honap,lpad(day(from_unixtime(o.timestamp)),2,0) nap,year(from_unixtime(o.timestamp)) ev, o.total, o.shipping_ids shipping, sd.description, case when o.shipping_ids in (12,1,13,11,6) then 'magánvásárló' when o.shipping_ids in (14,10,8,9) then 'viszonteladó' end csoport FROM cscart_orders o join cscart_statuses s on s.status=o.status and s.type='O' join cscart_status_descriptions sd on sd.status_id=s.status_id and sd.lang_code='hu' where from_unixtime(o.timestamp)>CURDATE()- INTERVAL 2 year and o.status in ('P', 'C', 'O', 'A', 'E', 'G', 'H')"
orders = readWEB(sqlQuery)
print('webstat queried') 
###

credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_FILE)


client = bigquery.Client(credentials=credentials)
table_id = BIGQUERY_PROJECT_ID + '.' + BIGQUERY_DATASET_ID + '.webshop_data'

try:
	job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
	job= client.load_table_from_dataframe(
		orders, table_id, job_config=job_config
	)
	job.result()  # Wait for the job to complete.
	print(f"Loaded {job.output_rows} rows into {table_id}.")
except Exception as error:
	notifyover('webstat',repr(error))