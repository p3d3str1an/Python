from os.path import dirname
from os.path import join
from pathlib import Path
import itertools
import re
import sys
import time

sweetfle = Path("sweet_user_pass.txt")
sweetfle.touch(exist_ok=True)

file = open("sweet_user_pass.txt")
line = file.readlines()

try:
    e_mail=line[0].strip()
except IndexError:
    e_mail = input('sweet.tv e-mail: ')
try:
    p_assw=line[1].strip()
except IndexError:
    p_assw = input('sweet.tv jelszó: ')

print(e_mail+'\n'+p_assw, file=open("sweet_user_pass.txt", "w", encoding="utf-8"))

print('\nSweet.tv bejelentkezés...', flush=True)

import requests

headers = {
    'authority': 'api.sweet.tv',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'hu',
    'content-type': 'application/json',
    'origin': 'https://sweet.tv',
    'referer': 'https://sweet.tv/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'x-accept-language': 'hu',
    'x-device': '1;22;0;2;4.0.54',
}

json_data = {
    'device': {
        'type': 'DT_Android_Player',
        'application': {
            'type': 'AT_SWEET_TV_Player',
        },
        'model': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'firmware': {
            'versionCode': 1,
            'versionString': '4.0.54',
        },
        'supported_drm': {
            'widevine_modular': True,
        },
        'screen_info': {
            'aspectRatio': 6,
            'width': 2048,
            'height': 1152,
        },
    },
    'email': e_mail,
    'password': p_assw,
}

response = requests.post('https://api.sweet.tv/SigninService/Email.json', headers=headers, json=json_data).json()

access_token = response['access_token']
bear = 'Bearer '+access_token
print(response['result'])
if response['result'] != 'OK':
    print(f'\n{response}')
    print('\n [INFO] ip címed bannolva lett valamennyi időre \n próbáld újra min. 45-60 perc múlva..')
    print(' vagy vpn-el válts ip címet...')
    ex_it = input('\n Kilépéshez Enter...')
    sys.exit(0)

import requests

headers3 = {
    'authority': 'api.sweet.tv',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'hu',
    'authorization': bear,
    'content-type': 'application/json',
    'origin': 'https://sweet.tv',
    'referer': 'https://sweet.tv/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    'x-accept-language': 'hu',
    'x-device': '1;22;0;2;5.3.00',
}

json_data3 = {
    'need_epg': False,
    'need_list': True,
    'need_offsets': False,
    'need_hash': False,
    'need_icons': True,
}

print('\nCsatorna lista letöltése...')
response3 = requests.post('https://api.sweet.tv/TvService/GetChannels.json', headers=headers3, json=json_data3).json()

cha_ids = []
for item_ids in response3['list']:
    ch_id_s = item_ids['id']
    cha_ids.append(f'{ch_id_s}')

cha_names = []
for item_names in response3['list']:
    names = item_names['name']
    names = re.sub('(RTL$)', 'RTL HD', names)
    names = re.sub('(TV2 HD$)', 'TV2', names)
    names = re.sub('(M1 HD$)', 'M1', names)
    names = re.sub('(Film\+ HD$)', 'Film+', names)
    names = re.sub('(MOZI\+ HD$)', 'Mozi+', names)
    names = re.sub('(MOZIVERZUM HD$)', 'Moziverzum', names)
    names = re.sub('(PRIME$)', 'Prime', names)
    names = re.sub('(M2 HD$)', 'M2', names)
    names = re.sub('(DUNA TV HD$)', 'DUNA', names)
    names = re.sub('(M5 HD$)', 'M5', names)
    names = re.sub('(DUNA WORLD HD$)', 'DUNA WORLD', names)
    names = re.sub('(M4 SPORT HD$)', 'M4 Sport', names)
    names = re.sub('(Sport 1 HD$)', 'Sport 1', names)
    names = re.sub('(Eurosport 1 HD$)', 'Eurosport', names)
    names = re.sub('(Sport 2 HD$)', 'Sport 2', names)
    names = re.sub('(Eurosport 2 HD$)', 'Eurosport 2', names)
    names = re.sub('(Arena 4 HD$)', 'Arena4', names)
    names = re.sub('(MATCH4 HD$)', 'Match 4', names)
    names = re.sub('(TV2 KIDS$)', 'Tv2 Kids', names)
    names = re.sub('(Minimax$)', 'Minimax', names)
    names = re.sub('(Disney Channel$)', 'Disney Channel', names)
    names = re.sub('(Nickelodeon HD$)', 'Nickelodeon', names)
    names = re.sub('(Nickelodeon Junior$)', 'Nick Jr.', names)
    names = re.sub('(Nicktoons$)', 'Nicktoons', names)
    names = re.sub('(TeenNick$)', 'TeenNick', names)
    names = re.sub('(Cartoon Network HD$)', 'Cartoon Network', names)
    names = re.sub('(Boomerang$)', 'Boomerang', names)
    names = re.sub('(Cartoonito HD$)', 'Cartoonito', names)
    names = re.sub('(Duck TV$)', 'Duck TV', names)
    names = re.sub('(JimJam$)', 'JimJam', names)
    names = re.sub('(Baby TV$)', 'Baby TV', names)
    names = re.sub('(SUPER TV2 HD$)', 'Super TV2', names)
    names = re.sub('(Cool TV HD$)', 'Cool TV', names)
    names = re.sub('(Viasat 3 HD$)', 'VIASAT3', names)
    names = re.sub('(AMC HD$)', 'AMC', names)
    names = re.sub('(AXN HD$)', 'AXN', names)
    names = re.sub('(Paramount Network HD$)', 'Paramount Channel', names)
    names = re.sub('(Film Mánia HD$)', 'Film Mania', names)
    names = re.sub('(VIASAT FILM$)', 'Viasat Film', names)
    names = re.sub('(Film 4$)', 'Film4', names)
    names = re.sub('(RTL HÁROM HD$)', 'RTL Harom', names)
    names = re.sub('(MTV Europe$)', 'MTV European', names)
    names = re.sub('(MTV 90s$)', 'MTV 90s', names)
    names = re.sub('(MTV 80s\'s$)', 'MTV 80s', names)
    names = re.sub('(RTL KETTŐ HD$)', 'RTL Ketto', names)
    names = re.sub('(TV 4 HD$)', 'TV4', names)
    names = re.sub('(Story 4 HD$)', 'Story4', names)
    names = re.sub('(Viasat 6$)', 'VIASAT6', names)
    names = re.sub('(E! Entertainment HD$)', 'E! Entertainment', names)
    names = re.sub('(Discovery HD$)', 'Discovery Channel', names)
    names = re.sub('(National Geographic HD$)', 'Nat Geo HD', names)
    names = re.sub('(Nat Geo Wild HD$)', 'Nat Geo Wild HD', names)
    names = re.sub('(Spektrum HD$)', 'Spektrum', names)
    names = re.sub('(Animal Planet HD$)', 'Animal Planet', names)
    names = re.sub('(BBC Earth HD$)', 'BBC Earth', names)
    names = re.sub('(Travel Channel HD$)', 'Travel', names)
    names = re.sub('(Viasat Explore HD$)', 'Viasat Explore', names)
    names = re.sub('(Viasat History HD$)', 'Viasat History', names)
    names = re.sub('(Viasat Nature HD$)', 'Viasat Nature', names)
    names = re.sub('(Discovery Turbo Xtra DTX HD$)', 'Discovery Turbo Xtra', names)
    names = re.sub('(Discovery Science HD$)', 'Discovery Science', names)
    names = re.sub('(ID Xtra Discovery Channel$)', 'Investigation Discovery', names)
    names = re.sub('(Spektrum Home HD$)', 'Spektrum Home', names)
    names = re.sub('(HGTV HD$)', 'HGTV', names)
    names = re.sub('(TLC HD$)', 'TLC', names)
    names = re.sub('(TV Paprika HD$)', 'TV Paprika', names)
    names = re.sub('(TV2 SÉF$)', 'Tv2 Sef', names)
    names = re.sub('(Food Network$)', 'Food Network', names)
    names = re.sub('(FEM3$)', 'FEM3', names)
    names = re.sub('(Hír TV HD$)', 'Hir TV', names)
    names = re.sub('(CNN HD$)', 'CNN', names)
    names = re.sub('(Euronews$)', 'Euronews', names)
    names = re.sub('(TV2 Comedy$)', 'TV2 Comedy', names)
    names = re.sub('(Comedy Central Family$)', 'Comedy Central Family', names)
    names = re.sub('(Comedy Central Hungary$)', 'Comedy_Central', names)
    names = re.sub('(RTL Gold$)', 'RTL Gold', names)
    names = re.sub('(Film Cafe HD$)', 'Film Cafe', names)
    names = re.sub('(Galaxy 4 HD$)', 'Galaxy4', names)
    names = re.sub('(Film 4 HD$)', 'Film4', names)
    names = re.sub('(IZAURA TV HD$)', 'Izaura TV', names)
    names = re.sub('(Sorozat\+$)', 'Sorozat+', names)
    names = re.sub('(JOCKY TV$)', 'Jocky TV', names)
    names = re.sub('(Epic Drama HD$)', 'Epic Drama HD', names)
    names = re.sub('(VIASAT 2$)', 'Viasat 2', names)
    names = re.sub('(CBS REALITY$)', 'CBS Reality', names)
    names = re.sub('(MTV 00\'s$)', 'MTV 00s', names)
    names = re.sub('(Club MTV$)', 'Club MTV', names)
    names = re.sub('(MTV Hits$)', 'MTV Hits', names)
    names = re.sub('(MTV Live HD$)', 'MTV Live', names)
    names = re.sub('(Life TV HD$)', 'LifeTV', names)
    names = re.sub('(Ozone TV HD$)', 'OzoneTV', names)
    names = re.sub('(ATV HD$)', 'ATV', names)
    names = re.sub('(ATV Spirit HD$)', 'ATV Spirit', names)
    names = re.sub('(ZENEBUTIK$)', 'Zenebutik', names)
    names = re.sub('(Muzsika TV$)', 'Muzsika TV', names)
    names = re.sub('(Mezzo HD$)', 'Mezzo', names)
    names = re.sub('(iConcerts HD$)', 'iConcerts', names)
    names = re.sub('(Brazzers HD$)', 'Brazzers TV Europe', names)
    names = re.sub('(PureBabes TV HD$)', 'PureBabes TV', names)
    names = re.sub('(Reality Kings HD$)', 'Reality Kings TV', names)
    names = re.sub('(Kölyök Klub HD$)', 'Kolyokklub', names)
    names = re.sub('(Mozi Klub)', 'Moziklub', names)
    names = re.sub('(Sorozat Klub)', 'SorozatKlub', names)
    names = re.sub('(RTL Otthon HD$)', 'RTL_Otthon', names)
    names = re.sub('(Food Network HD$)', 'Food_Network', names)    
    cha_names.append(f'{names}')

cha_numbers = []
for item_numbers in response3['list']:
    numbers = item_numbers['number']
    cha_numbers.append(f'{numbers}')

cha_logos = []
for item_logos in response3['list']:
    logos = item_logos['icon_v2_url']
    cha_logos.append(f'{logos}')

channelsNum = len(cha_numbers)
print(f'\nElérhető csatornák: {channelsNum}')

print('\nCsatorna linkek betöltése...')
hls_links = []
for index, get_ids in enumerate(cha_ids, start=1):
    import requests
    
    headers2 = {
        'authority': 'api.sweet.tv',
        'accept-language': 'hu',
        'authorization': bear,
        'content-type': 'application/json',
        'origin': 'https://sweet.tv',
        'referer': 'https://sweet.tv/',
        'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="102"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'x-device': '1;22;0;2;4.0.50',
    }
    
    json_data2 = {
        'without_auth': True,
        'channel_id': get_ids,
        'accept_scheme': [
            'HTTP_HLS',
        ],
        'multistream': True,
    }    
    
    response2 = requests.post('https://api.sweet.tv/TvService/OpenStream.json', headers=headers2, json=json_data2).json()    

    time.sleep(3)
    
    Unavailable = response2['result']
    if Unavailable == 'UnavailableInSubscription':
        print('\nehhez nincs hozzáférés az account-al..\ntovábblépés a következőre\n')
        continue
    
    ht_p1 = 'https://'
    try:
        ht_p2 = response2['http_stream']['host']['address']
    except KeyError:
        print('\n [ERROR] jelszó/passz lejárt...')
        ex_it = input(' Kilépéshez Enter...')
        sys.exit(0)
    
    ht_p3 = response2['http_stream']['url'] 
    ht_togeth = ht_p1+ht_p2+ht_p3

    hls_links.append(f'{ht_togeth}')

    print('+', end='', flush=True)
    if index % 10 == 0:
        print(index, end=' ', flush=True)


print("\nAz m3u8 fájlok generálása...")
f=open("sweet_kodi.m3u8", "w", encoding="utf-8")
print('#EXTM3U',file=f)
for (names, numbers, logo, m3u8_links) in zip(cha_names, cha_numbers, cha_logos, hls_links):
     print(f'#EXTVLCOPT:http-user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"\n#EXTINF:0, tvg-chno={numbers}, tvg-logo={logo}, {names}\n{m3u8_links}', file=f)


f2=open("sweet_vlc.m3u8", "w", encoding="utf-8")
print('#EXTM3U',file=f2)
for (names, numbers, m3u8_links) in zip(cha_names, cha_numbers, hls_links):
     print(f'#EXTVLCOPT:http-user-agent="Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36"\n#EXTINF:0,{numbers}, {names}\n{m3u8_links}', file=f2)

print('\nAz m3u8 fájlok frissítve lettek. :)\n')