import pyodbc
import sys
import pandas as pd
import xlwings as xw
from auDAOlib import readPROD, finish

picPath = 'D:\\Arsuna\\TERMEKKEPEK\\ppp200\\'
xlsPath = 'D:\\Arsuna\\piclist.xlsx'

sqlQuery = """
select i.itemcode, i.codebars, i.itemname
from ARSUNA_2020_PROD.dbo.oitm i 
where itemcode in (
    '94748161', '94748178', '94749168', '94749182', '94749199', '94749502', '94749519', '94749588', '94758146', '94758153', '94758160', '94758177', '94758443', '94758450', '94758467', '94758474', '94758481', '94758498', '94758894', '94759167', '94759198', '94759501', '94759518', '94759525', '94759549', '94759570', '94759594', '94759600', '95105680', '95109671', '95109688', '95109695', '95109718', '95109725', '95015378', '95015613', '95015668', '95015675', '95015682', '95019673', '95019697', '95019703', '95019710', '95019727'
)
"""
dfStock = readPROD(sqlQuery)

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
	try:
		pic = worksheet.pictures.add(imagefile, top = worksheet.range((rownum,4)).top+5, left= worksheet.range((rownum,4)).left+5, width=100, height=100)
		pic.width=100
		pic.height=100
	except:
		print(imagefile) 

finish()