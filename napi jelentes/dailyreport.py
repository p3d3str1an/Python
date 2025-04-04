import sys
from auDAOlib import readASSIST, execASSIST, notify
from datetime import datetime, timedelta
import pandas
from credentials import KOZOSPATH, MYLOCALPATH


execASSIST('napi')
nap = datetime.now()-timedelta(days=1) # datetime.strptime('20210219',"%Y%m%d")
outputPath = KOZOSPATH+r'\adatok\napi jelentés\tmp\nr' + str(nap.strftime("%y%m%d")) + '.xlsx'
reportPath = MYLOCALPATH+r'\Desktop\report-forg.xlsm'
result = readASSIST('select * from napijelentes')
if isinstance(result, pandas.DataFrame):
	result.to_excel(outputPath, index=False)
else:
	notify('hiba a napijelentésben')