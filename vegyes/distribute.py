# ez valami régiség, nem is tudom mit csinál

import xlwings as xw
from credentials import MYLOCALPATH

xlsPath = MYLOCALPATH+r'\OneDrive\ArsUna\DTW\Raktár\alap.xlsx'


sourceWB = xw.Book(xlsPath)
sourceWS = sourceWB.sheets['input']
outputWS = sourceWB.sheets['output']


A_end = sourceWS.range('A:A').end('down').row
B_end = sourceWS.range('B:B').end('down').row
C_end = sourceWS.range('C:C').end('down').row

distribute = sourceWS.range((1, 1), (A_end, 1)).value
column1 = sourceWS.range((1, 2), (B_end, 2)).value
column2 = sourceWS.range((1, 3), (C_end, 3)).value
column3 = sourceWS.range((1, 4), (sourceWS.range('D:D').end('down').row, 4)).value

row = 1

for i, entry in enumerate(distribute):
	for i2, col1 in enumerate(column1):
		outputWS.range(row, 1).value = entry
		outputWS.range(row, 2).value = col1
		outputWS.range(row, 3).value = column2[i2]
		outputWS.range(row, 4).value = column3[i2]
		row+=1