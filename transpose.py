import csv


csv.register_dialect("semicolon", delimiter=";")

with open(r'C:\Users\p3d3str1an\OneDrive\ArsUna\vegyes\source.csv') as f:
    reader = csv.reader(f)
    data = list(reader)

line=''
counter=0
for row in data:
    counter+=1
    line+=r"'"+row[0]+r"',"
    if counter%20==0:
        line+='\n'


with open(r'C:\Users\p3d3str1an\OneDrive\ArsUna\vegyes\output.csv', mode='w') as csvFile:
    csvWriter = csv.writer(csvFile, dialect='semicolon', quoting = csv.QUOTE_NONE, escapechar=' ')
    csvWriter.writerow([line[:-1]])
#    csvWriter.writerow([line])