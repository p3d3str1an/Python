import sys
from auDAOlib import readASSIST, execASSIST, notifyover, notifymail, readPROD
from datetime import datetime, timedelta
import pandas
from credentials import KOZOSPATH, MYLOCALPATH

# Napi jelentés készítése

execASSIST('napi')
nap = datetime.now()-timedelta(days=1) # datetime.strptime('20210219',"%Y%m%d")
outputPath = KOZOSPATH+r'\adatok\napi jelentés\tmp\nr' + str(nap.strftime("%y%m%d")) + '.xlsx'
reportPath = MYLOCALPATH+r'\Desktop\report-forg.xlsm' #ezt valószínűleg azért tettem ide, hogy majd a report is automatikusan készüljön el, de még nincs kész
result = readASSIST('select * from napijelentes')
if isinstance(result, pandas.DataFrame):
	result.to_excel(outputPath, index=False)
else:
	notifyover('hiba a napijelentésben')



# Ide fog kerülni az a checks.py-ből, aminek elég naponta egyszer lefutnia

#Ildinek számlaküldés hiányok listája:
notsentquery = """
	select 'számla' tipus, i.docnum, i.cardname, i.cardcode, dbo.timeconvert(i.docdate, i.doctime) ido
	from oinv i
	join ocrd c on c.CardCode=i.CardCode
	where c.GroupCode = '102' 
	and not exists (select oalr.code from oalr join aob1 on aob1.AlertCode=oalr.code where oalr.attachment like '%'+cast(i.docnum as varchar)+'%' and aob1.Confirmed2='Y')
	and i.DocDate>'2025-01-01'
	and i.cardcode not in ('134011467', 'partnerkedv')
	and i.Series not in ('538')
	and i.docstatus='O'
	and i.docnum not in ('4005789','4005245','4005810')

	union all
	select 'jóváírás', i.docnum, i.cardname, i.cardcode, dbo.timeconvert(i.docdate, i.doctime) ido
	from orin i
	join ocrd c on c.CardCode=i.CardCode
	where c.GroupCode = '102' 
	and not exists (select oalr.code from oalr join aob1 on aob1.AlertCode=oalr.code where oalr.attachment like '%'+cast(i.docnum as varchar)+'%' and aob1.Confirmed2='Y')
	and i.DocDate>'2025-01-01'
	and i.cardcode not in ('134011467', 'partnerkedv')
	and i.Series not in ('538')
"""
notsentlist = readPROD(notsentquery)
body= str(notsentlist.to_string(index=False, header=False, columns=['tipus', 'docnum', 'cardname']))
if notsentlist.shape[0]>0:
	notifymail('it@arsuna.hu', 'Kiküldetlen számlák', body)