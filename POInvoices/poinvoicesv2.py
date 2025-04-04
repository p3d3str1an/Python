import pyodbc
import pandas as pd

''' thanks to https://github.com/peterkulik/ois_api_client '''

import ois_api_client as ois


from datetime import datetime, timezone, timedelta
import sys
import re
import auDAOlib
import params
from ois_api_client.v3_0 import dto, deserialization
import xml.etree.ElementTree as ET
from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER



def last_day_of_month(any_day):
	next_month = any_day.replace(day=28) + timedelta(days=4)
	return next_month - timedelta(days=next_month.day)


# dátumintervallum, max 35 nap

defaultFromDate = datetime.now().replace(day=1).strftime("%Y-%m-%d")
defaultToDate = last_day_of_month(datetime.now()).strftime("%Y-%m-%d")

while True:
	fromDate = input("Kezdődátum (" + defaultFromDate + "): ") or defaultFromDate
	toDate = input("Záródátum: (" + defaultToDate + "): ") or defaultToDate
	try:
		dateFrom = datetime.strptime(re.sub('[-,. /]','',fromDate if len(fromDate)>4 else str(datetime.today().year)+fromDate), "%Y%m%d")
		dateTo = datetime.strptime(re.sub('[-,. /]','',toDate if len(toDate)>4 else str(datetime.today().year)+toDate), "%Y%m%d")
	except ValueError:
		print("Hibás dátum formátum. Kérlek, próbáld újra (YYYYMMDD vagy YYYY-MM-DD).")
		continue

	if abs((dateTo - dateFrom).days) > 35:
		print('Több mint 35 nap, nem fogja engedni a NAV. Kérlek, adj meg rövidebb intervallumot.')
		continue
	else:
		break

outputPath = params.outputPath
missingPath = params.missingPath
accpath = params.accpath
outputHeaderPath = outputPath+r'\bejovoszla-header.csv'
outputLinePath = outputPath+r'\bejovoszla-lines.csv'
szallitoQRY = r"select distinct CardCode, CardName, isnull(substring(u_addid,3,8),substring(LicTradNum,3,8)) LicTradNum, LicTradNum as VATCode from ocrd where cardtype='S' and LicTradNum like 'HU%'"
szamlaQRY = r"""select distinct isnull(isnull(numatcard,'')+isnull(substring(ocrd.u_addid,3,8),substring(ocrd.LicTradNum,3,8)),'-') id from OPCH join ocrd on ocrd.cardcode=opch.cardcode
				union all
				select distinct isnull(isnull(numatcard,'')+isnull(substring(ocrd.u_addid,3,8),substring(ocrd.LicTradNum,3,8)),'-') id from ODRF join ocrd on ocrd.cardcode=odrf.cardcode where odrf.ObjType=18"""

defaultAcctCodes = dict(pd.read_excel(accpath).values)

client = ois.Client(uri='https://api.onlineszamla.nav.gov.hu/invoiceService/v3')

def _() -> ois.HeaderFactoryParameters:
	return ois.HeaderFactoryParameters(
		login=NAV_USERNAME,
		tax_number=NAV_TAX_NUMBER,
		password=NAV_PASSWORD,
		signature_key=NAV_SIGNATURE_KEY
	)
make_headers = ois.header_factory.make_default_header_factory(load_parameters=_)


software = dto.Software(
	software_id='HU10772335AU-00002',
	software_name='ARSUNA incoming invoice import',
	software_operation=dto.SoftwareOperation.LOCAL_SOFTWARE,
	software_main_version='2.0',
	software_dev_name='Kovács Krisztián',
	software_dev_contact='it@arsuna.hu',
	software_dev_country_code='HU',
	software_dev_tax_number='73584454')


def digest_request_build(oldal):
	header, user_header = make_headers()
	return dto.QueryInvoiceDigestRequest(
			header=header,
			user=user_header,
			software=software,
			page=oldal,
			invoice_direction=dto.InvoiceDirection.INBOUND,
			invoice_query_params=dto.InvoiceQueryParams(
				mandatory_query_params= dto.MandatoryQueryParams(
					invoice_issue_date=dto.DateIntervalParam(date_from=dateFrom,date_to=dateTo),
					ins_date=None,
					original_invoice_number=None
					),
				additional_query_params=None,
				relational_query_params=None,
				transaction_query_params=None)
		)

def detail_request(szamla):
	header, user_header = make_headers()
	data_request = dto.QueryInvoiceDataRequest(
		header=header,
		user=user_header,
		software=software,
		invoice_number_query=dto.InvoiceNumberQuery(
			invoice_number=szamla.invoice_number,
			invoice_direction=dto.InvoiceDirection.INBOUND,
			batch_index=None,
			supplier_tax_number=szamla.supplier_tax_number
		))

	try:
		data_response = client.query_invoice_data(data_request)
		invoice_xml = ois.decode_invoice_data(data_response.invoice_data_result)
		xml_root = ET.fromstring(invoice_xml)
		invoice_data = deserialization.deserialize_invoice_data(xml_root)
		return invoice_data
	except ois.GeneralError as err:
		gen_err: dto.GeneralErrorResponse = dto.deserialize_general_error_response(err.general_error_response)
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
	if invoice.invoice_category == dto.InvoiceCategory.SIMPLIFIED:
		invoice_data = detail_request(invoice)
		header['DocTotal'] = invoice_data.invoice_main.invoice.invoice_summary.summary_gross_data.invoice_gross_amount
		if invoice_data.invoice_main.invoice.invoice_summary.summary_simplified[0].vat_rate.vat_percentage:
			print(invoice_data.invoice_main.invoice.invoice_head.supplier_info.supplier_name+" - "+ invoice_data.invoice_main.invoice.invoice_summary.summary_simplified[0].vat_rate.vat_percentage)
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
	general_error_response_xml = ET.fromstring(err.general_error_response)
	gen_err: dto.GeneralErrorResponse = deserialization.deserialize_general_error_response(general_error_response_xml)
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
dfSuppliers = auDAOlib.readPROD(szallitoQRY)
print('már beolvasott számlák listája')
dfPOInvoices = auDAOlib.readPROD(szamlaQRY)


print('beolvasandó számlák listájának összeállítása')
dfInvExportHeaderCols = pd.DataFrame(columns = ['DocEntry', 'Doctype', 'DocObjectCode', 'CardCode', 'NumAtCard', 'DocDate', 'TaxDate', 'DocDueDate', 'VatDate', 'DocTotal', 'Comments', 'DocCurrency'], dtype = 'str')
dfInvExportHeaderRow = pd.DataFrame([['DocEntry', 'Doctype', 'DocObjectCode', 'CardCode', 'NumAtCard', 'DocDate', 'TaxDate', 'DocDueDate', 'VatDate', 'DocTotal', 'Comments', 'DocCurrency']], columns=dfInvExportHeaderCols.columns)
dfInvExportHeader = pd.concat([dfInvExportHeaderCols, dfInvExportHeaderRow])
dfInvExportLinesCols = pd.DataFrame(columns= ['Docentry', 'LineNum', 'AccountCode', 'Price'], dtype = 'str')
dfInvExportLinesRow = pd.DataFrame([['Docentry', 'LineNum', 'AccountCode', 'Price']], columns=dfInvExportLinesCols.columns)
dfInvExportLines = pd.concat([dfInvExportLinesCols, dfInvExportLinesRow])
missingSuppliers = set([])
missingSup = pd.DataFrame(columns = ['LicTradNum', 'Cardname'])

for idx, invoice in enumerate(digest_list):
	if len(dfPOInvoices[dfPOInvoices['id']==invoice.invoice_number+(invoice.supplier_group_member_tax_number or invoice.supplier_tax_number)].index)<1:		#ha nincs még a rendszerben ilyen számlaszám+adószám kombóval bizonylat
			if len(dfSuppliers[dfSuppliers['LicTradNum']==invoice.supplier_tax_number].index)>0: 															#de létezik a partner már az SBOban
				cardcode = dfSuppliers.CardCode[dfSuppliers.LicTradNum==invoice.supplier_tax_number].iloc[0]		  										#kikeressük a partnerlistából az azonosítót
				headersor = headerFill(idx, invoice)
				linesor = lineFill(idx, cardcode, invoice)
				dfInvExportHeader = pd.concat([dfInvExportHeader,pd.DataFrame([headersor], columns=headersor.keys())])
				dfInvExportLines = pd.concat([dfInvExportLines,pd.DataFrame([linesor], columns=linesor.keys())])
			else:
				supplierdata = {'LicTradNum':[invoice.supplier_tax_number], 'Cardname':[invoice.supplier_name]}  # ez engem zavar, hogy egy egyelemű listát kell csinálni a dict-ben, de a from_dict miatt kell
				if invoice.supplier_tax_number not in missingSup['LicTradNum']:
					supplierpd = pd.DataFrame.from_dict(supplierdata)
					missingSup = pd.concat([missingSup,supplierpd], ignore_index=True)
print('fájlok exportja')
dfInvExportHeader.to_csv(outputHeaderPath, sep=';', index=False, encoding='ansi')
dfInvExportLines.to_csv(outputLinePath, sep=';', index=False, encoding='ansi')
missingSup.to_excel(missingPath, index=False)
input('művelet kész')