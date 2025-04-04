import pyodbc
import sys
import pandas as pd
import xlwings as xw
from auDAOlib import readPROD


picPath = 'D:\\Arsuna\\TERMEKKEPEK\\ppp200\\'
xlsPath = 'D:\\Arsuna\\AUrendeles2025.xlsx'

arlista = 23
akciodatum = r"'2025-03-15'"
nemakciodatum = r"'2025-03-03'"


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
sum(be.OpenQty) beszerzes, coalesce(min(o.beerkezes), min(be.docduedate), '2025.05.10') bedatum, i.u_id, sum(i.onhand) keszlet, i.ItmsGrpCod
from ARSUNA_2020_PROD.dbo.oitm i 
join arsuna_2020_prod.dbo.oitw w on w.whscode=120 and w.itemcode=i.itemcode
left join AUassist.dbo.orderform o on o.cikkszam=i.itemcode
left join
    (select pl.itemcode, pl.OpenQty, iif(ph.docduedate>getdate(),ph.DocDueDate,null) docduedate from ARSUNA_2020_PROD.dbo.por1 pl join ARSUNA_2020_PROD.dbo.opor ph on ph.DocEntry=pl.DocEntry and ph.DocStatus='O' where pl.LineStatus='O'
    union all
    select bl.itemcode, bl.OpenQty, iif(bh.vatdate>getdate(),bh.vatdate,null) docduedate from ARSUNA_2020_PROD.dbo.pch1 bl join ARSUNA_2020_PROD.dbo.opch bh on bh.DocEntry=bl.DocEntry and bh.DocStatus='O' where bl.LineStatus='O' and bh.isins='Y') be on be.ItemCode=i.ItemCode
where i.itemname not like '%kulacstet%' and i.itemname not like '%szilikon%' and i.ItmsGrpCod not in (103) and i.itemcode not in ('1004') and u_id not in ('581', '633', '637')
group by i.ItemCode, i.CodeBars, i.ItemName, i.u_id,  i.ItmsGrpCod
having ((sum(be.OpenQty)>0) or i.itemcode in (select id from auassist.dbo.temp))
and (sum(i.onhand)=0 or i.itemcode in (select id from auassist.dbo.temp))
and i.itemcode not in ('56635171','56634600','56634570','56634815','56635195','56633764','56653908','56653915','56653922','56653939','56655209','56333985','56373905','56373912','56373929','56373936','56375206','56333909','55814669','50212859', 
'50492855','52543593','52543760','53562852','53563590','53833495','56645187')
union all
select ean8, ean13, cikknev, csomegys, 
case {arlista} when 1 then nk when 18 then ot when 20 then tiz when 21 then tizenot when 23 then husz end ar, 
case when cikknev like '%lambo%' then 
    case {arlista} when 1 then nk when 18 then ot when 20 then tiz when 21 then tizenot when 23 then husz end
else 
    case {arlista} when 1 then nk when 18 then ot when 20 then tiz when 21 then tizenot when 23 then husz end*.95
end kedvar,
0,beerkezes, id, 0, null
from AUassist.dbo.orderform_extra) ttt
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
