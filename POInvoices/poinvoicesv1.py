'''

elavult script, közben frissült az api client,
csak történeti érdekesség miatt hagyom itt, a v2-t használom

'''


import pyodbc
import pandas as pd

''' thanks to https://github.com/peterkulik/ois_api_client '''

import ois_api_client as ois

from datetime import datetime, timezone, timedelta
import sys
import re
import auDAOlib
import params
from credentials import NAV_PASSWORD, NAV_USERNAME, NAV_SIGNATURE_KEY, NAV_REPLACEMENT_KEY, NAV_TAX_NUMBER

def last_day_of_month(any_day):
	# this will never fail
	# get close to the end of the month for any day, and add 4 days 'over'
	next_month = any_day.replace(day=28) + timedelta(days=4)
	# subtract the number of remaining 'overage' days to get last day of current month, or said programattically said, the previous day of the first of next month
	return next_month - timedelta(days=next_month.day)


# dátumintervallum, max 35 nap

defaultFromDate = datetime.now().replace(day=1).strftime("%Y-%m-%d")
defaultToDate = last_day_of_month(datetime.now()).strftime("%Y-%m-%d")

fromDate = input("Kezdődátum (" + defaultFromDate + "): ") or defaultFromDate
toDate = input("Záródátum: (" + defaultToDate + "): ") or defaultToDate

dateFrom = datetime.strptime(re.sub('[-,. /]','',fromDate if len(fromDate)>4 else str(datetime.today().year)+fromDate), "%Y%m%d")
dateTo = datetime.strptime(re.sub('[-,. /]','',toDate if len(toDate)>4 else str(datetime.today().year)+toDate), "%Y%m%d")

if abs((dateTo - dateFrom).days)>35:
	input('Több mint 35 nap, nem fogja engedni a NAV')
	sys.exit()

outputPath = params.outputPath
missingPath = params.missingPath
accpath = params.accpath
outputHeaderPath = outputPath+r'\bejovoszla-header.csv'
outputLinePath = outputPath+r'\bejovoszla-lines.csv'
sqlQuery = r"select distinct CardCode, CardName, isnull(substring(u_addid,1,8),substring(LicTradNum,3,8)) LicTradNum, LicTradNum as VATCode from ocrd where cardtype='S' and LicTradNum like 'HU%'"
sqlQuery2 = r"""	select distinct isnull(isnull(numatcard,'')+isnull(substring(ocrd.u_addid,1,8),substring(ocrd.LicTradNum,3,8)),'-') id from OPCH join ocrd on ocrd.cardcode=opch.cardcode
						union all
						select distinct isnull(isnull(numatcard,'')+isnull(substring(ocrd.u_addid,1,8),substring(ocrd.LicTradNum,3,8)),'-') id from ODRF join ocrd on ocrd.cardcode=odrf.cardcode where odrf.ObjType=18"""

defaultAcctCodes = dict(pd.read_excel(accpath, engine='openpyxl').values)

client = ois.Client(
	uri='https://api.onlineszamla.nav.gov.hu/invoiceService/v3',	
	signature_key=NAV_SIGNATURE_KEY,
	replacement_key=NAV_REPLACEMENT_KEY,
	password=NAV_PASSWORD)

user = ois.UserHeader(
	login=NAV_USERNAME,
	tax_number=NAV_TAX_NUMBER,)

software = ois.Software(
	id='HU10772335AU-00002',
	name='ARSUNA M-lap parser',
	operation='LOCAL_SOFTWARE',
	main_version='1.1',
	dev_name='Kovács Krisztián',
	dev_contact='it@arsuna.hu',
	dev_country_code='HU',
	dev_tax_number='73584454')


def digest_request_build(oldal):
	return ois.QueryInvoiceDigestRequest(
			header=ois.BasicHeader(
				request_id='AU'+str(int(datetime.now().timestamp()))+str(oldal),
				timestamp=datetime.now().astimezone(tz=timezone.utc)),
			user=user,
			software=software,
			page=oldal,
			invoice_direction=ois.InvoiceDirection.INBOUND,
			invoice_query_params=ois.InvoiceQueryParams(
				ois.MandatoryQueryParams(
						ois.MandatoryQueryParams.InvoiceIssueDate(
							ois.DateIntervalParam(
								date_from=dateFrom,
								date_to=dateTo,
							))))
		)

def detail_request(szamla):

	data_request = ois.QueryInvoiceDataRequest(
		header=ois.BasicHeader(
			request_id='AU'+str(int(datetime.now().timestamp()))+str(szamla.index),
			timestamp=datetime.now()),
		user=user,
		software=software,
		invoice_number_query=ois.InvoiceNumberQuery(
			invoice_number=szamla.invoice_number,
			invoice_direction=ois.InvoiceDirection.INBOUND,
			batch_index=None,
			supplier_tax_number=szamla.supplier_tax_number
		))

	try:
		data_response = client.query_invoice_data(data_request)
		invoice_xml_as_string = ois.decode_invoice_data(data_response.invoice_data_result.invoice_data)
		print(invoice_xml_as_string)
	except ois.GeneralError as err:
		gen_err: ois.GeneralErrorResponse = ois.deserialize_general_error_response(err.general_error_response)
		print(gen_err.result.message)
		print(gen_err.result.error_code)
		print(gen_err.result.func_code)

		for tvm in gen_err.technical_validation_messages:
			print(tvm.message)
			print(tvm.validation_error_code)
			print(tvm.validation_result_code)
	except Exception as err:
		print(err)

def headerFill(idx, invoice):
	header = {}
	header['DocEntry'] = int(idx)
	header['Doctype'] = 'S'
	header['DocObjectCode'] = '18'
	header['CardCode'] = cardcode
	header['NumAtCard'] = invoice.invoice_number
	header['DocDate'] = invoice.invoice_delivery_date.strftime("%Y-%m-%d") if invoice.invoice_delivery_date else None
	header['TaxDate'] = invoice.invoice_issue_date.strftime("%Y-%m-%d") if invoice.invoice_issue_date else None
	header['VatDate'] = invoice.invoice_delivery_date.strftime("%Y-%m-%d") if invoice.invoice_delivery_date else None
	header['DocDueDate'] = invoice.payment_date.strftime("%Y-%m-%d") if invoice.payment_date else None
	if invoice.invoice_net_amount_huf is None:
		header['DocTotal'] = 0
	else:
		header['DocTotal']= invoice.invoice_net_amount_huf+invoice.invoice_vat_amount_huf
	header['Comments'] = invoice.original_invoice_number
	header['DocCurrency'] = invoice.currency if (invoice.currency!='HUF') else 'Ft'
	return header

def lineFill(idx, cardcode, invoice):
	line = {}
	line['Docentry'] = int(idx)
	line['LineNum'] = 0
	if invoice.invoice_net_amount_huf is None:
		line['Price'] = 0
		line['PriceAfterVAT'] = 0
	else:
		line['Price'] = invoice.invoice_net_amount_huf
		line['PriceAfterVAT'] = invoice.invoice_net_amount_huf+invoice.invoice_vat_amount_huf
	line['AccountCode'] = str(defaultAcctCodes.get(cardcode) or '5139000')
	return line


digest_request = digest_request_build(1)

print('1. oldal lekérése')
try:
	digest_response = client.query_invoice_digest(digest_request)
	digest_list = digest_response.invoice_digest_result.invoice_digest

	for page in range(1,digest_response.invoice_digest_result.available_page+1):
		if page>1:
			print(str(page) + '. oldal lekérése')
			digest_request = digest_request_build(page)
			digest_response = client.query_invoice_digest(digest_request)
			digest_list += digest_response.invoice_digest_result.invoice_digest

except ois.GeneralError as err:
	gen_err: ois.GeneralErrorResponse = ois.deserialize_general_error_response(err.general_error_response)
	print(gen_err.result.message)
	print(gen_err.result.error_code)
	print(gen_err.result.func_code)

	for tvm in gen_err.technical_validation_messages:
		print(tvm.message)
		print(tvm.validation_error_code)
		print(tvm.validation_result_code)
except Exception as err:
	print(err)

print('szállítók listája')
dfSuppliers = auDAOlib.readPROD(sqlQuery)
print('már beolvasott számlák listája')
dfPOInvoices = auDAOlib.readPROD(sqlQuery2)


print('beolvasandó számlák listájának összeállítása')
dfInvExportHeader = pd.DataFrame(columns = ['DocEntry', 'Doctype', 'DocObjectCode', 'CardCode', 'NumAtCard', 'DocDate', 'TaxDate', 'DocDueDate', 'VatDate', 'DocTotal', 'Comments', 'DocCurrency'], dtype = 'str')
dfInvExportHeader = dfInvExportHeader.append(pd.Series(('DocEntry', 'Doctype', 'DocObjectCode', 'CardCode', 'NumAtCard', 'DocDate', 'TaxDate', 'DocDueDate', 'VatDate', 'DocTotal', 'Comments', 'DocCurrency'), index=dfInvExportHeader.columns),ignore_index=True)
dfInvExportLines = pd.DataFrame(columns= ['Docentry', 'LineNum', 'AccountCode', 'Price'], dtype = 'str')
dfInvExportLines = dfInvExportLines.append(pd.Series(('Docentry', 'LineNum', 'AccountCode', 'Price'),index=dfInvExportLines.columns),ignore_index=True)
missingSuppliers = set([])
missingSup = pd.DataFrame(columns = ['LicTradNum', 'Cardname'])

for idx, invoice in enumerate(digest_list):
	if len(dfPOInvoices[dfPOInvoices['id']==invoice.invoice_number+(invoice.supplier_group_tax_number or invoice.supplier_tax_number)].index)<1:				#ha nincs még a rendszerben ilyen számlaszám+adószám kombóval bizonylat
			if len(dfSuppliers[dfSuppliers['LicTradNum']==invoice.supplier_tax_number].index)>0: 																				#de létezik a partner már az SBOban
				cardcode = dfSuppliers.CardCode[dfSuppliers.LicTradNum==invoice.supplier_tax_number].iloc[0]		  													#kikeressük a partnerlistából az azonosítót
				headersor = headerFill(idx, invoice)
				linesor = lineFill(idx, cardcode, invoice)
				dfInvExportHeader = dfInvExportHeader.append(headersor, ignore_index=True)
				dfInvExportLines = dfInvExportLines.append(linesor,ignore_index=True)
			else:
#				missingSuppliers.add(invoice.supplier_tax_number + '\t' +invoice.supplier_name)
				supplierdata = {'LicTradNum':invoice.supplier_tax_number, 'Cardname':invoice.supplier_name}
				if invoice.supplier_tax_number not in missingSup['LicTradNum']:
					missingSup = missingSup.append(supplierdata, ignore_index=True)
				#detail_request(invoice)
print('fájlok exportja')
dfInvExportHeader.to_csv(outputHeaderPath, sep=';', index=False, encoding='ansi')
dfInvExportLines.to_csv(outputLinePath, sep=';', index=False, encoding='ansi')
#with open(missingPath, "w") as outfile:
#	outfile.write("\n".join(missingSuppliers))
missingSup.to_excel(missingPath, index=False)
#print('missing suppliers:')
#print(missingSuppliers)
input('művelet kész')