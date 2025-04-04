import os
import xlrd
from credentials import MYLOCALPATH

inputPath = MYLOCALPATH+'/OneDrive/ArsUna/Multik/Pirex/Pirex bizós jelentések 2019/'
ean = '94498387'
sum = 0

for root, dirs, files in os.walk(inputPath):
	for name in files:
		fullPath=os.path.join(root, name)
		workBook = xlrd.open_workbook(fullPath)
		sheet = workBook.sheet_by_index(0)
		for row in range(sheet.nrows):
			row_values = sheet.row_values(row)
			if row_values[5] == ean:
				print(str(name)+' sor:'+str(row)+' db '+str(row_values[3]))
				sum+=row_values[3]
print(sum)
