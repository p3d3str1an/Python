import mysql.connector
from mysql.connector import Error
#from phpserialize import cursor
from credentials import DATABASES

try:
	connection = mysql.connector.connect(host=DATABASES['ARSUNAHU']['host'],
	 									port=DATABASES['ARSUNAHU']['port'],
                                       	database=DATABASES['ARSUNAHU']['database'],
                                       	user=DATABASES['ARSUNAHU']['username'],
                                       	password=DATABASES['ARSUNAHU']['password'])
except Error as e:
    print("Error while connecting to MySQL", e)


query = """
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

cursor = connection.cursor()
cursor.execute(query)
#records = cursor.fetchall()
print('affected: ' + str(cursor.rowcount))
connection.commit()