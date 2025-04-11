import gspread
import os
from oauth2client.service_account import ServiceAccountCredentials
from auDAOlib import notifyover, readPROD, readWEB
import pandas as pd 

scope = ["https://spreadsheets.google.com/feeds",'https://www.googleapis.com/auth/spreadsheets',"https://www.googleapis.com/auth/drive.file","https://www.googleapis.com/auth/drive"]
currdir = os.getcwd()
creds = ServiceAccountCredentials.from_json_keyfile_name(currdir+r"\gcreds.json", scope) # json file with credentials
client = gspread.authorize(creds)
spreadsheet = client.open("grafana-stat")

# datapython
sqlQuery = '''
			;WITH SalesYTD AS (
				SELECT
					ev,
					dat AS nap,
					SUM(nettó) AS daily_sum
				FROM AUAssist.dbo.sales
				WHERE ev >= 2021 AND ytd = 'I'
				GROUP BY ev, dat
			),
			Cumulative AS (
				SELECT
					ev,
					nap,
					SUM(daily_sum) OVER (PARTITION BY ev ORDER BY nap) AS cumulative_sum
				FROM SalesYTD
			)
			SELECT
				nap as time,
				MAX(CASE WHEN ev = 2021 THEN cumulative_sum END) AS [2021],
				MAX(CASE WHEN ev = 2022 THEN cumulative_sum END) AS [2022],
				MAX(CASE WHEN ev = 2023 THEN cumulative_sum END) AS [2023],
				MAX(CASE WHEN ev = 2024 THEN cumulative_sum END) AS [2024],
				MAX(CASE WHEN ev = 2025 THEN cumulative_sum END) AS [2025]
			FROM Cumulative
			GROUP BY nap
			ORDER BY nap;
			'''
df = readPROD(sqlQuery)
print('grafanastat queried')

# --- FIX: Convert datetime objects to strings ---
# Check if the 'time' column exists and is of datetime type
if 'time' in df.columns and pd.api.types.is_datetime64_any_dtype(df['time']):
	# Format as 'YYYY-MM-DD HH:MM:SS' string. Google Sheets and Grafana usually parse this well.
	df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
	print('Converted time column to string format for upload.')
elif 'time' not in df.columns:
		raise ValueError("DataFrame is missing the required 'time' column.")
# If 'time' exists but isn't datetime, we assume it's already serializable (e.g., string)
# --- End of fix ---

# Optional: Ensure 'value' column is numeric before upload if needed
if 'value' in df.columns:
	df['value'] = pd.to_numeric(df['value'], errors='coerce') # Convert non-numbers to NaN

# Prepare data list for update (handle potential NaN values from coerce)
# Replace NaN with empty strings as gspread/Sheets handle this better
df_for_upload = df.fillna('')
list_to_upload = [df_for_upload.columns.values.tolist()] + df_for_upload.values.tolist()




# Cumulative sum per year
#df.sort_values(['year', 'date'], inplace=True)
#df['cumulative_sum'] = df.groupby('year')['daily_sum'].cumsum()

# Reshape for Grafana
#df['metric'] = 'Year ' + df['year'].astype(str)
#df_grafana = df[['date', 'metric', 'cumulative_sum']].rename(columns={
#    'date': 'time',
#    'cumulative_sum': 'value'
#})


try:
	worksheet = spreadsheet.worksheet('values')
	worksheet.clear()
	worksheet.update(list_to_upload, value_input_option='USER_ENTERED')
	print('grafanastat passed')
except Exception as error:
	# Print the error locally for easier debugging
	print(f"ERROR updating Google Sheet: {error}")
	notifyover('grafanastat',repr(error))                                                                                                                                                 