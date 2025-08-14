from google.cloud import bigquery
from google.oauth2 import service_account
from auDAOlib import notifyover, readWEB, readPROD, setup_logging
from credentials import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET_ID, GOOGLE_APPLICATION_CREDENTIALS_FILE
import logging

credentials = service_account.Credentials.from_service_account_file(GOOGLE_APPLICATION_CREDENTIALS_FILE)
client = bigquery.Client(credentials=credentials)
setup_logging(log_filename='webstat.log',place=0)

# webstat 
sqlQuery = r"SELECT o.order_id, from_unixtime(o.timestamp, '%Y%m%d') date,lpad(month(from_unixtime(o.timestamp)),2,0) honap,lpad(day(from_unixtime(o.timestamp)),2,0) nap,year(from_unixtime(o.timestamp)) ev, o.total, o.shipping_ids shipping, sd.description, case when o.shipping_ids in (12,1,13,11,6) then 'magánvásárló' when o.shipping_ids in (14,10,8,9) then 'viszonteladó' end csoport FROM cscart_orders o join cscart_statuses s on s.status=o.status and s.type='O' join cscart_status_descriptions sd on sd.status_id=s.status_id and sd.lang_code='hu' where from_unixtime(o.timestamp)>CURDATE()- INTERVAL 2 year and o.status in ('P', 'C', 'O', 'A', 'E', 'G', 'H')"
webshop_data = readWEB(sqlQuery)
logging.info(f"Webshop data queried, {len(webshop_data)} rows found.")
print('webstat queried') 
###

sqlQueryPending = r"select	count(distinct drf1.docentry) as tervezetkod from odrf join	drf1 on drf1.docentry=odrf.docentry where drf1.baseentry in (select docentry from ordr where docstatus='O') and drf1.basetype=17 and odrf.DocStatus='O' and odrf.docentry not in (137708)"
pendingOrders = readPROD(sqlQueryPending)
logging.info(f"Pending orders queried")

tables_to_upload = {
	'webshop_data': webshop_data,
	'pendingOrders': pendingOrders
}



for table_name, df in tables_to_upload.items():
	if df.empty:
		logging.warning(f"No data found for table '{table_name}'. Skipping upload.")
		continue
	logging.info(f"Uploading table '{table_name}'...")
	# Construct the full table ID
	table_id = f"{BIGQUERY_PROJECT_ID}.{BIGQUERY_DATASET_ID}.{table_name}"

	# Configure the load job. We'll overwrite the table each time.
	job_config = bigquery.LoadJobConfig(
		write_disposition="WRITE_TRUNCATE",
	)

	# Start the load job from the DataFrame
	try:
		job = client.load_table_from_dataframe(
			df, table_id, job_config=job_config
		)
		job.result()  # Wait for the job to complete
		logging.info(f"Table '{table_name}' uploaded successfully.")
	except Exception as e:
		logging.error(f"Failed to upload table '{table_name}': {e}")
		notifyover('webstat',repr(e))
logging.info("All tables uploaded successfully.")