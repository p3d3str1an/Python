# API teszt

from base64 import b64encode
import requests
import json
from pandas import read_excel
from credentials import ARSUNAHU_TESZT22_API_KEY, ARSUNAHU_ELES_API_KEY

def query(param):
	return baseurl+param

teszt = False; #ezt állítsd true ha tesztelni szeretnél 
listapath = r'C:\Users\p3d3str1an\OneDrive\ArsUna\Python\hozzajarulas.xlsx'

if teszt:
	authstring = "it@arsuna.hu:"+ARSUNAHU_TESZT22_API_KEY
	baseurl = 'https://teszt22.arsuna.hu/api/'
else:
	authstring = "it@arsuna.hu:"+ARSUNAHU_ELES_API_KEY
	baseurl = 'https://arsuna.hu/api/'
tokenstring = "basic " + b64encode(authstring.encode("utf-8")).decode("utf-8")
my_headers = {"Authorization": tokenstring}
my_headers['Content-type']='application/json'
my_headers['User-Agent'] ='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
param = 'products?free_shipping=Y'


headerstring = ''
for k,v in my_headers.items():
	headerstring +=" -H '"+k+":"+v+"'"
curlstring = "curl " + headerstring + " -X GET " + "'" + baseurl+param + "'"

#curlstring csak a teszteléshez lett összerakva
#print(curlstring)


response = requests.get(query(param), headers=my_headers, allow_redirects=False)



print(response.content)

