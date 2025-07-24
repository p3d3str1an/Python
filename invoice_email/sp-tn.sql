/* Következő SQL-t be kell szúrni a SBO_SP_TransactionNotification eljárásba, ha megvan a felhasználói tábla:
[EMAIL_OBJECTS] (code, name, objtype, docentry, statusz, result, email)
a táblának 'No object with auto increment' típusúnak kell lennie, a name-be megy a bizonylatszám
a működéshez feltételezzük, [IFSZ_TRF_BIZONYLAT_FEJ] tábla létezik, és benne vannak a webshopból importált bizonylatok adatai, amiből a webes azonosító valahogy bekerült a számla u_webszám felh.mezőjébe
(nálunk az is tranz.notiffal megy)
 */


  IF  @error = 0  AND  ( @object_type = '13' )  AND  ( @transaction_type = 'A' )
 
  BEGIN
	insert into [@EMAIL_OBJECTS]
    select i.docnum, '13' objtype,i.docentry, 'TS' statusz, 'notsent' as result, case when i.cardcode like 'WEB%' then trf.EMAIL else isnull(c_szall.u_emaillista,isnull(c_szla.u_emaillista,c.E_Mail)) end email
    from oinv i 
    left join ifsz_trf_bizonylat_fej trf on trf.biz_azon=substring(i.u_webszam,charindex('#',u_webszam)+1,len(i.u_webszam))
    join ocrd c on c.CardCode=i.CardCode
    left join crd1 c_szla on c_szla.cardcode=c.cardcode and c_szla.address=i.paytocode
	left join crd1 c_szall on c_szall.CardCode=c.CardCode and c_szall.Address=i.ShipToCode
    where i.docentry= @list_of_cols_val_tab_del
    and i.CardCode not in ('bolt', 'boltszla', '14410160', '134009621', '134011539', '7340170', '134009240', '14490008', '134010986', '134011563', '2290082', '134011436', 'magy', 'signo', 'laser', '13400761', 'partnerkedv', '134011469', '134011409') -- kivételek, nekik kézzel küldjük a számlákat 
	and c.GroupCode not in ('102')
	and i.series not in (551,539, 540, 553)
  END;

  --------------------------------------------------------------------------------------------------------------------------------
  if  @error <> 0  goto vege;




