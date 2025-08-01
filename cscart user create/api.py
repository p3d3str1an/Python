# CS Cart felhasználók létrehozása egy Excel lista alapján

from base64 import b64encode
import requests
import json
from pandas import read_excel
from credentials import ARSUNAHU_TESZT22_API_KEY, ARSUNAHU_ELES_API_KEY, MYLOCALPATH
from auDAOlib import setup_logging
import logging

setup_logging(log_filename='cscart_user_create.log', place=2)

def query(param):
	return baseurl+param

teszt = False; #ezt állítsd true ha tesztelni szeretnél 
listapath = MYLOCALPATH+r'\OneDrive\Python\cscart user create\hozzajarulas.xlsx' 


# FONTOS, az apiadminnak nem lehet a cscart_usergroup_links táblában bejegyzése, mert akkor nem tudja létrehozni a felhasználókat! 

if teszt:
	authstring = "apiadmin@arsuna.hu:"+ARSUNAHU_TESZT22_API_KEY
	baseurl = 'https://teszt22.arsuna.hu/api/'
else:
	authstring = "apiadmin@arsuna.hu:"+ARSUNAHU_ELES_API_KEY
	baseurl = 'https://arsuna.hu/api/'
tokenstring = "basic " + b64encode(authstring.encode("utf-8")).decode("utf-8")
my_headers = {"Authorization": tokenstring}
my_headers['Content-type']='application/json; charset=utf-8'
my_headers['User-Agent'] ='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
headerstring = ''
for k,v in my_headers.items():
	headerstring +=" -H '"+k+":"+v+"'"


lista = read_excel(listapath, usecols='A:C', dtype={'phone': str}).to_dict("records") # columns: lastname, phone, email

# userek létrehozása
list_length = len(lista)

for index, listaitem in enumerate(lista):

	createuser = listaitem | {"company_id":"1", "status":"A","user_type":"C"}
	user = json.dumps(createuser, ensure_ascii=False).encode('utf-8')
	param = 'users'
	response = requests.post(query(param), headers=my_headers, data=user)
		

# ha sikerült, akkor mehet a Törzsvásárlók közé
	if response.status_code==201:
		my_headers['Content-type']='application/json'
		updateuser_id=str(json.loads(response.content)['user_id'])
		d=json.dumps({"company_id":"1","status":"A"})
		param ='users/'+updateuser_id+'/usergroups/10'
		responseupdate = requests.post(query(param), headers=my_headers, data=d)
		logging.info(f"{index + 1}/{list_length}: " + createuser['email'] + " hozzáadva")
	else:
		logging.error(response.json()['message'])
		logging.error(f"{index + 1}/{list_length}: "+ createuser['email'] + " nem sikerült létrehozni a felhasználót")
