import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from auDAOlib import notifyover, readPROD

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
currdir = os.getcwd()
creds = ServiceAccountCredentials.from_json_keyfile_name(currdir+r"\gcreds.json", scope)
client = gspread.authorize(creds)
spreadsheet5 = client.open("fullitemstat")

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
print('fullitemstat queried')


try:
	worksheet5 = spreadsheet5.worksheet('data')
	worksheet5.clear()
	worksheet5.update([sales5.columns.values.tolist()] + sales5.values.tolist())
	print('fullitemstat.data filled')
except Exception as error:
	notifyover('fullitemstat',repr(error))          