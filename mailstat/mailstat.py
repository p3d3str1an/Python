import mysql.connector
from mysql.connector import Error
from phpserialize import unserialize
from datetime import datetime
from collections import Counter
from auDAOlib import notifyover
from credentials import DATABASES

# init
#limit = sys.argv[1]
limit = 1500
note=''

# DAO - átírandó a readWEB megoldással
try:
	connection = mysql.connector.connect(host=DATABASES['ARSUNAHU']['host'],
	 									port=DATABASES['ARSUNAHU']['port'],
                                       	database=DATABASES['ARSUNAHU']['database'],
                                       	user=DATABASES['ARSUNAHU']['username'],
                                       	password=DATABASES['ARSUNAHU']['password'])
	logfile = open("mailstat_log.txt", "w")
except Error as e:
	notifyover('Mailstat','Error while connecting to MySQL')

# query 24 hour runtime logs
query = "select *,timestamp time from cscart_logs where action='runtime' and timestamp>unix_timestamp(CURRENT_TIMESTAMP())-86400 order by timestamp;"

cursor = connection.cursor()
cursor.execute(query)
records = cursor.fetchall()

emailto = {}
mails = []
noti = False

# extract and count sender email
for i, record in enumerate(records):
	rec = unserialize(bytes(record[7], 'utf8'))
	if rec[b'message']==b'Mail. Success:ok':
		emailto['mail']=rec[b'mail_user'].decode('utf8')
		emailto['time']=record[10]
		mails.append(emailto.copy())

c = Counter([m['mail'] for m in mails])
# notify if above limit
for key in c:
	count = c[key]
	lasttime = max([t['time'] for t in mails if t.get('mail') == key])
	logfile.write(key.split('@')[0] + ' ' + str(count) + ' last: ' + datetime.fromtimestamp(lasttime).strftime('%y-%m-%d %H:%M:%S') + '\n')
	note += key.split('@')[0] + ' ' + str(c[key]) + chr(10)
	if count > limit:
		noti = True


if noti:
#	notifyfrom('Mailstat', note)
	notifyover('Mailstat', note)

query2 = """
	insert into cscart_usergroup_links (user_id, usergroup_id, status)
	SELECT 
	u.user_id, 10, 'A'
	FROM cscart_em_subscribers s
	inner join cscart_users u on u.email=s.email
	left join cscart_usergroup_links l on u.user_id=l.user_id and l.usergroup_id=10
	left join cscart_usergroup_links lv on u.user_id=lv.user_id and lv.usergroup_id=5
	where
	(ifnull(l.status,'N') <> 'A' and ifnull(lv.status,'N') not in ('A', 'N'))
	and s.status='A'
"""


cursor.execute(query2)
logfile.write('torzsv. affected: ' + str(cursor.rowcount) + '\n')

"""  ezt inkább kézzel, akciupdate.sql a mysql folderemben
cursor.execute("insert ignore into cscart_product_features_values (feature_id, product_id, value, lang_code) select 11, product_id, 'N', lang_code from cscart_products join cscart_languages")
logfile.write('new discounted items: ' + str(cursor.rowcount) + '\n')
cursor.execute ("update cscart_product_features_values set value='N' where feature_id=11")
logfile.write('all discount to null: ' + str(cursor.rowcount) + '\n')
cursor.execute("update cscart_product_features_values set value='Y' where feature_id=11 and product_id in (select cscart_product_id from oitm where u_akcios='I')")
logfile.write('actual discounted items: ' + str(cursor.rowcount) + '\n')

 """

connection.commit()



	
logfile.close()
	
#input("Press Enter to continue...")
