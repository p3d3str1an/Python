import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from auDAOlib import notifyover, readPROD, readWEB

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
currdir = os.getcwd()
creds = ServiceAccountCredentials.from_json_keyfile_name(currdir+r"\gcreds.json", scope) # json file with credentials
client = gspread.authorize(creds)
spreadsheet = client.open("grafana-stat")

# datapython
sqlQuery = r"SELECT ev AS year, CAST(datum AS date) AS date, SUM(nettó) AS daily_sum FROM AUAssist.dbo.sales WHERE ev >= 2021 AND DATEPART(dy, datum) <= (SELECT MAX(DATEPART(dy, datum)) FROM AUAssist.dbo.sales WHERE ev = YEAR(GETDATE())) GROUP BY ev, CAST(datum AS date)"
df = readPROD(sqlQuery)
print('grafanastat queried')


# Cumulative sum per year
df.sort_values(['year', 'date'], inplace=True)
df['cumulative_sum'] = df.groupby('year')['daily_sum'].cumsum()

# Reshape for Grafana
df['metric'] = 'Year ' + df['year'].astype(str)
df_grafana = df[['date', 'metric', 'cumulative_sum']].rename(columns={
    'date': 'time',
    'cumulative_sum': 'value'
})


try:
	worksheet = spreadsheet.worksheet('values')
	worksheet.clear()
	worksheet.update([df_grafana.columns.values.tolist()] + df_grafana.values.tolist())
	print('grafanastat passed')
except Exception as error:
	notifyover('grafanastat',repr(error))                                                                                                                                                 