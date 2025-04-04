import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from auDAOlib import notifyover, readPROD, readWEB

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
currdir = os.getcwd()
creds = ServiceAccountCredentials.from_json_keyfile_name(currdir+r"\gcreds.json", scope) # json file with credentials
client = gspread.authorize(creds)
spreadsheet = client.open("stat")
spreadsheet2 = client.open("fullstat")
spreadsheet4 = client.open("webstat")
spreadsheet5 = client.open("fullitemstat")

# datapython
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', vnev, ev, month(datum) honap FROM AUAssist.dbo.sales where ev>='2021' group by vevőcsoport, vevőcsop2, vkód, vnev, ev, month(datum)"
sales = readPROD(sqlQuery)
print('datapython queried')

# fullstat
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum FROM AUAssist.dbo.sales where ev>='2021' group by vevőcsoport, vevőcsop2, vkód, ev, month(datum), datum"
sales2 = readPROD(sqlQuery)
print('fullstat queried')

# ytdstat
sqlQuery = r"SELECT sum(nettó) osszeg, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum, datepart(dy,datum) ytd FROM AUAssist.dbo.sales where ev>='2021' and datepart(dy,datum)<=(select max(datepart(dy,datum)) from AUAssist.dbo.sales where ev=year(getdate())) group by vevőcsoport, vevőcsop2, vkód, ev, month(datum), datum"
sales3 = readPROD(sqlQuery)
print('ytdstat queried')

# webstat 
sqlQuery = r"SELECT o.order_id, from_unixtime(o.timestamp, '%Y%m%d') date,lpad(month(from_unixtime(o.timestamp)),2,0) honap,lpad(day(from_unixtime(o.timestamp)),2,0) nap,year(from_unixtime(o.timestamp)) ev, o.total, o.shipping_ids shipping, sd.description FROM cscart_orders o join cscart_statuses s on s.status=o.status and s.type='O' join cscart_status_descriptions sd on sd.status_id=s.status_id and sd.lang_code='hu' where from_unixtime(o.timestamp)>CURDATE()- INTERVAL 2 year and o.status in ('P', 'C', 'O', 'A', 'E', 'G', 'H')"
sales4 = readWEB(sqlQuery)
print('webstat queried') 
###


### kiszedve a harmadik sorból ez (ytd): and datepart(dy,datum)<=(select max(datepart(dy,datum)) from AUAssist.dbo.sales where ev=2021), mert a ytdstatot a sales3 query nézi 

# fullitemstat
sqlQuery5 = '''
				SELECT id, cikknev, sum(nettó) osszeg, sum(darab) as db, vevőcsoport, vevőcsop2 csoport, vkód 'vevőkód', ev, month(datum) honap, cast(datum as date) datum, datepart(dy,datum) ytd,
				case when vkód in ('WEB', 'WEBC', 'bolt', 'boltszla') then 'magánvásárló' else 'viszonteladó' end vevotipus 
				FROM AUAssist.dbo.sales 
				where ev>'2021' 
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
	print('webstat passed')
except Exception as error:
	notifyover('sales4',repr(error))                                                                                                                                                 

try:
	# ez külön fájlban van, mert ritkábban frissül, mint a többi
	#worksheet5 = spreadsheet5.worksheet('data')
	#worksheet5.clear()
	#worksheet5.update([sales5.columns.values.tolist()] + sales5.values.tolist())
	print('fullitemstat.data filled')
except Exception as error:
	notifyover('fullitemstat',repr(error))