from auDAOlib import notifyover, readPROD, readWEB
# nem kell már a requests, csak ha a complete_trf pótlására kellene
# import requests


msg=''

# elakadt webes rendelés

result = readPROD(
	r"""
	SELECT
        [BIZ_AZON]
      , [HIBA]
      , [FELDOLGOZANDO_E]      
      , [SBO_CARDCODE]
      , cast([SBO_CNTCTCODE] as nvarchar) "Partner/Száll"
      , [EU_VAT]
      , [NEV]
      , [SZAMLA_NEV]
      , [SZALL_NEV]
    FROM [ARSUNA_2020_PROD].[dbo].[IFSZ_TRF_BIZONYLAT_FEJ]
    where FELDOLGOZAS_DATUMA is null and ELUTASITVA_E<>'I' and isnull(MEGJEGYZES,'') not LIKE '%H'
	"""
)
if result.shape[0]>0:
	msg+='Web: '+str(result.shape[0])


# elakadt tabletes rendelés

result = readPROD(
	r"""
   SELECT
        [ManualNum]
      , [ERROR_MSG]
      , [Transzferalva]
      , [CardCode]
      , [ShipToCode]
      , ''
      , [Comments]
      , [QUEUE_ID]
      , [DOCNUM]
    FROM [ARSUNA_2020_PROD].[dbo].[IFSZ_UK_ORDR]
    where Transzferalva not in('I','D','T')
	"""
)

if result.shape[0]>0:
	msg+=chr(10) + ' Visz: '+str(result.shape[0])

# webes és SBO-s rendelés végösszege különbözik

result = readPROD(
		r"""
		select 
		f.BIZ_AZON --,f.id, r.docnum, r.NumAtCard, r.cardname, r.docdate, r.doctime, r.doctotal, f.total, r.Printed, r.Comments
		from ordr r
		join ifsz_trf_bizonylat_fej f on f.BIZ_AZON=r.NumAtCard
		where r.docdate>'2021-08-01'
		and abs(r.doctotal-f.total)>1000
		and r.cardcode like 'WEB%'
		and r.CardCode not like 'WEBEUR'
		and right(r.Comments,1) not in ('T', 'J', 'H', 'M')
	"""
)

if result.shape[0]>0:
	msg+=chr(10) + ' ÁFAhiba: '+ str(result['BIZ_AZON'].values)


# levélküldési hiba

result = readPROD(
		r"""
      select 
      distinct o.Subject, a.NameFrom,  a.[Status], b.WasSent, dbo.timeconvert(b.SendDate, b.SendTime) sent, cast(o.Attachment as varchar(100)) attachment 
      --count(*) db
      from alr1 a
          join oalr o on o.code=a.code
          join oaob b on b.AlertCode=o.Code 
          join aob1 b1 on b1.AlertCode=o.Code
      where (a.Status='U' and datediff(mi, dbo.timeconvert(b.SendDate, b.SendTime), getdate())>10)
      or (a.[Status]='E' and b.SendDate>dateadd(day,-1,getdate()))
	    and (a.code not in (11143, 11128, 11126))
	"""
)

if result.shape[0]>0:
	msg+=chr(10) + ' Mailerhiba: '+ str(result.shape[0])


# webes státuszváltási hiba

draftresult = readPROD(
	r"""
    SELECT numatcard
    FROM ODRF T0 
    left join oslp t1 on t1.slpcode=t0.slpcode
    inner join nnm1 t2 on t2.series=t0.series
    left join oshp t4 on t4.trnspcode=t0.trnspcode
    where T0.ObjType=17 and t0.Docstatus='O' and t2.Seriesname like 'WEB%'

    union all
    	SELECT
      [BIZ_AZON]
    	FROM [ARSUNA_2020_PROD].[dbo].[IFSZ_TRF_BIZONYLAT_FEJ]
    	where  isnull(MEGJEGYZES,'') LIKE '%H'
  """
)

draft = ", ".join(f"'{s}'" for s in draftresult['numatcard'].values.tolist())

result = readWEB(
  fr"""
  select  
	o.order_id,
    o.email AS email,
    o.total as total,
    o.notes AS megjegyzes,
    from_unixtime(o.timestamp) AS datum, date_sub(now(), INTERVAL 40 MINUTE)
  from cscart_orders o
  where 
  o.status='O'
  and from_unixtime(o.timestamp)<date_sub(now(), INTERVAL 40 MINUTE)
  and o.order_id not in ({draft}) and o.order_id not in (123127, 123929)
  """
)

if result.shape[0]>0:
	msg+=chr(10) + ' Complete_trf: '+str(result.shape[0])

# webes rendelés el se indult

result1 = readWEB(
	r"select order_id from cscart_orders where order_id > 140000 and status<>'N' and from_unixtime(timestamp)<date_sub(now(), INTERVAL 40 MINUTE)"
)['order_id'].unique()

result2 = readPROD(
	r"select cast(biz_azon as int) as order_id from ifsz_trf_bizonylat_fej where atadva>'2024-01-01'"
)['order_id'].unique()

missingorders=[x for x in result1 if x not in result2]

if len(missingorders)>0:
	msg+=chr(10) + ' Missingorder: '+str(missingorders)

# Számlaküldési hiba

result = readPROD(
		r"""
    select name
    from [@EMAIL_OBJECTS] Where U_status='ER'
    and code>1060
	"""
)

if result.shape[0]>0:
	msg+=chr(10) + ' Számlahiba: '+ str(result.shape[0])


#complete_trf pótlása, mert az interface nem tudja megnyitni - megoldódott

#my_headers={'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'}
#response = requests.get('<php helye>', headers=my_headers)

#if response.status_code != 200:
#    msg+=chr(10) + 'Complete_trf: '+ str(response.status_code)

#hibaüzenetek kiküldése

if msg!='':
#	notify(msg)
	notifyover('Checks', msg)
