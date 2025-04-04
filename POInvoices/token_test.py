import xml.etree.ElementTree as ET
import ois_api_client as ois
from ois_api_client.v3_0 import dto, deserialization
from credentials import NAV_SIGNATURE_KEY, NAV_PASSWORD, NAV_USERNAME, NAV_TAX_NUMBER



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
	software_name='ARSUNA incoming invoice import token test',
	software_operation=dto.SoftwareOperation.LOCAL_SOFTWARE,
	software_main_version='2.0',
	software_dev_name='Kovács Krisztián',
	software_dev_contact='it@arsuna.hu',
	software_dev_country_code='HU',
	software_dev_tax_number='73584454')


client = ois.Client(uri='https://api.onlineszamla.nav.gov.hu/invoiceService/v3', timeout=30)
header, user_header = make_headers()

request = dto.BasicOnlineInvoiceRequest(
	header=header,
	user=user_header,
	software=software
)

try:
	response = client.token_exchange(request)
except ois.GeneralError as err:
	xmlroot = ET.fromstring(err.general_error_response)
	gen_err: dto.GeneralErrorResponse = deserialization.deserialize_general_error_response(xmlroot)
	print(gen_err.result.message)
	print(gen_err.result.error_code)
	print(gen_err.result.func_code)

	for tvm in gen_err.technical_validation_messages:
		print(tvm.message)
		print(tvm.validation_error_code)
		print(tvm.validation_result_code)
except Exception as err:
	print(err)





assert response is not None
assert response.result is not None
assert response.encoded_exchange_token is not None
assert len(response.encoded_exchange_token) > 0
assert response.token_validity_from is not None
assert response.token_validity_to is not None
assert response.result.error_code is None
assert response.result.message is None
assert response.result.func_code == dto.FunctionCode.OK