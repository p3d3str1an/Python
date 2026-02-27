import pyodbc
import sys
import pandas as pd
import xlwings as xw
from auDAOlib import readPROD


picPath = 'D:\\Arsuna\\TERMEKKEPEK\\ppp200\\'
xlsPath = 'D:\\Arsuna\\AUrendeles2026.xlsx'

arlista = 1
akciodatum = r"'2026-03-05'"
nemakciodatum = r"'2026-03-20'"


""" 1 - nagyker
12 - webnettó
18 - 5
20-10
21-15
23-20
9-pirex
17-regio """



sqlQuery = f"""

select * from
(select i.itemcode, i.codebars, i.itemname, min(i.salpackun) csomag, 
min(dbo.listaar({arlista},{nemakciodatum}, i.itemcode)) nkar, 
min(dbo.listaar({arlista},{akciodatum}, i.itemcode)) kedvar, 
sum(be.OpenQty) beszerzes, coalesce(min(o.beerkezes), min(be.docduedate), '2026.12.31') bedatum, i.u_id, sum(i.onhand) keszlet, i.ItmsGrpCod
from ARSUNA_2020_PROD.dbo.oitm i 
left join arsuna_2020_prod.dbo.oitw w on w.whscode=120 and w.itemcode=i.itemcode
left join AUassist.dbo.orderform o on o.cikkszam=i.itemcode
left join
    (select pl.itemcode, pl.OpenQty, iif(ph.docduedate>getdate(),ph.DocDueDate,null) docduedate from ARSUNA_2020_PROD.dbo.por1 pl join ARSUNA_2020_PROD.dbo.opor ph on ph.DocEntry=pl.DocEntry and ph.DocStatus='O' where pl.LineStatus='O'
    union all
    select bl.itemcode, bl.OpenQty, iif(bh.vatdate>getdate(),bh.vatdate,null) docduedate from ARSUNA_2020_PROD.dbo.pch1 bl join ARSUNA_2020_PROD.dbo.opch bh on bh.DocEntry=bl.DocEntry and bh.DocStatus='O' where bl.LineStatus='O' and bh.isins='Y') be on be.ItemCode=i.ItemCode
where 1=1
and i.ItmsGrpCod not in (103) -- borítékos lap
and i.itemcode not in ('1004') -- gyártási költségek

-- volt még több kiszedés, pl. egy rakat ean8, meg a kulacstetők és szilikonok, emlékeztetőül.

group by i.ItemCode, i.CodeBars, i.ItemName, i.u_id,  i.ItmsGrpCod
having ((sum(be.OpenQty)>0) or i.itemcode in (select id from auassist.dbo.temp))
and (sum(i.onhand)=0 or i.itemcode in (select id from auassist.dbo.temp))
) ttt
order by 1,2

"""


dfStock = readPROD(sqlQuery)
dfStock.sort_values(by=['u_id'])

if not isinstance(dfStock, pd.DataFrame):
	print(dfStock)
	sys.exit

workbook = xw.Book(xlsPath)
worksheet = workbook.sheets['ArsUna']
for i, row in dfStock.iterrows():
	rownum = i+2
	imagefile = picPath+row['itemcode']+'.jpg'
#	print(row)
	worksheet.range((rownum,1)).value=row['itemcode']
	worksheet.range((rownum,2)).value=row['codebars']
	worksheet.range((rownum,3)).value=row['itemname']
	worksheet.range((rownum,4)).value=row['bedatum']
	worksheet.range((rownum,5)).value=row['nkar']
	worksheet.range((rownum,6)).value=row['kedvar']
	worksheet.range((rownum,7)).value=row['csomag']
	worksheet.range((rownum,9)).value='=RC[-3]*RC[-1]'

	try:
		pic = worksheet.pictures.add(imagefile, top = worksheet.range((rownum,10)).top+5, left= worksheet.range((rownum,10)).left+5, width=100, height=100)
		pic.width=100
		pic.height=100
	except:
		print(imagefile) 
