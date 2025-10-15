import requests

# SOAP endpoint and headers
url = "https://api-onlinepenztargep.nav.gov.hu/queryCashRegisterFile/v1/queryCashRegisterStatus"
headers = {
		'Content-Type': 'application/xml',
        'Accept': 'application/xml'
}

# SOAP request body
soap_body = """<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" xmlns:api="http://schemas.nav.gov.hu/OPF/1.0/api" xmlns:com="http://schemas.nav.gov.hu/NTCA/1.0/common"> <soap:Header/> <soap:Body> <api:QueryCashRegisterStatusRequest> <com:header> <com:requestId>RID_1063C778-E821-4B90-BAF0-475118D2BE1A</com:requestId> <com:timestamp>2025-08-15T12:57:12.805Z</com:timestamp> <com:requestVersion>1.0</com:requestVersion> <com:headerVersion>1.0</com:headerVersion> </com:header> <com:user> <com:login>qek1ucndnsfah7q</com:login> <com:passwordHash cryptoType="SHA-512">E93D734491FE0F93A061457837A67846190D164CFD6ABB5E2530F3016FF3CD6B3DFF1513474273731E843D979BE1D2ECD0E94B2189E7F44252A622E504DC2440</com:passwordHash> <com:taxNumber>10772335</com:taxNumber> <com:requestSignature cryptoType="SHA3-512">CE8EB9F9B877382B506535292EACD7DFEDA8BB691B65339C6E56B4EF71AE332E5297C3EC7C9FD26F0DCC332F440465F9B96E89A179D05DD596F0F743668D760E</com:requestSignature> <!--<signKey>ac-ac3a-7f661bff7d342N43CYX4U9FG</signKey>--> </com:user> <api:software> <api:softwareId>HU10772335AU-AU-R001</api:softwareId> <api:softwareName>ARSUNA receipts downloader</api:softwareName> <api:softwareOperation>LOCAL_SOFTWARE</api:softwareOperation> <api:softwareMainVersion>1.0</api:softwareMainVersion> <api:softwareDevName>Kovacs Krisztian</api:softwareDevName> <api:softwareDevContact>it@arsuna.hu</api:softwareDevContact> <api:softwareDevCountryCode>HU</api:softwareDevCountryCode> <api:softwareDevTaxNumber>73584454</api:softwareDevTaxNumber> </api:software> <api:cashRegisterStatusQuery> <api:APNumberList> <api:APNumber>A00203368</api:APNumber> </api:APNumberList> </api:cashRegisterStatusQuery> </api:QueryCashRegisterStatusRequest> </soap:Body></soap:Envelope>"""


soap_body = '''
<soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope" xmlns:base="http://schemas.nav.gov.hu/OPF/1.0/cashregister" xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns:api="http://schemas.nav.gov.hu/OSA/3.0/api">\n  <soapenv:Body>\n    <base:QueryCashRegisterFileRequest>\n      <common:header>\n        <common:requestId>RID_58044E67-9CB0-4833-9291-3F5CF39960AE</common:requestId>\n        <common:timestamp>2025-08-15T13:57:32.565Z</common:timestamp>\n        <common:requestVersion>1.0</common:requestVersion>\n        <common:headerVersion>1.0</common:headerVersion>\n      </common:header>\n      <common:user>\n        <common:login>qek1ucndnsfah7q</common:login>\n        <common:passwordHash cryptoType="SHA-512">E93D734491FE0F93A061457837A67846190D164CFD6ABB5E2530F3016FF3CD6B3DFF1513474273731E843D979BE1D2ECD0E94B2189E7F44252A622E504DC2440</common:passwordHash>\n        <common:taxNumber>10772335</common:taxNumber>\n        <common:requestSignature cryptoType="SHA3-512">F32EA81A8BBFF4C5FCA65BF7E1CDE727BF3EFDD1F6542798B27651E3417A9063A92BA69DB38D11B9EBB142E015EDDE0816223227E16F34F868A428D8364269F9</common:requestSignature>\n      </common:user>\n      <api:software>\n        <softwareId>HU10772335AU-AU-R001</softwareId>\n        <softwareName>ARSUNA receipts downloader gemini</softwareName>\n        <softwareOperation>LOCAL_SOFTWARE</softwareOperation>\n        <softwareMainVersion>1.0</softwareMainVersion>\n        <softwareDevName>Kovács Krisztián - Gemini 2.5 pro</softwareDevName>\n        <softwareDevContact>it@arsuna.hu</softwareDevContact>\n      </api:software>\n      <base:cashRegisterFileQuery>\n        <cashRegisterId>A00203368</cashRegisterId>\n        <fromNumber>1</fromNumber>\n        <toNumber>1</toNumber>\n      </base:cashRegisterFileQuery>\n    </base:QueryCashRegisterFileRequest>\n  </<soapenv:Envelope xmlns:soapenv="http://www.w3.org/2003/05/soap-envelope" xmlns:base="http://schemas.nav.gov.hu/OPF/1.0/cashregister" xmlns:common="http://schemas.nav.gov.hu/NTCA/1.0/common" xmlns:api="http://schemas.nav.gov.hu/OSA/3.0/api">
  <soapenv:Body>
    <base:QueryCashRegisterFileRequest>
      <common:header>
        <common:requestId>RID_58044E67-9CB0-4833-9291-3F5CF39960AE</common:requestId>
        <common:timestamp>2025-08-15T13:57:32.565Z</common:timestamp>
        <common:requestVersion>1.0</common:requestVersion>
        <common:headerVersion>1.0</common:headerVersion>
      </common:header>
      <common:user>
        <common:login>qek1ucndnsfah7q</common:login>
        <common:passwordHash cryptoType="SHA-512">E93D734491FE0F93A061457837A67846190D164CFD6ABB5E2530F3016FF3CD6B3DFF1513474273731E843D979BE1D2ECD0E94B2189E7F44252A622E504DC2440</common:passwordHash>
        <common:taxNumber>10772335</common:taxNumber>
        <common:requestSignature cryptoType="SHA3-512">F32EA81A8BBFF4C5FCA65BF7E1CDE727BF3EFDD1F6542798B27651E3417A9063A92BA69DB38D11B9EBB142E015EDDE0816223227E16F34F868A428D8364269F9</common:requestSignature>
      </common:user>
      <api:software>
        <softwareId>HU10772335AU-AU-R001</softwareId>
        <softwareName>ARSUNA receipts downloader gemini</softwareName>
        <softwareOperation>LOCAL_SOFTWARE</softwareOperation>
        <softwareMainVersion>1.0</softwareMainVersion>
        <softwareDevName>Kovács Krisztián - Gemini 2.5 pro</softwareDevName>
        <softwareDevContact>it@arsuna.hu</softwareDevContact>
      </api:software>
      <base:cashRegisterFileQuery>
        <cashRegisterId>A00203368</cashRegisterId>
        <fromNumber>1</fromNumber>
        <toNumber>1</toNumber>
      </base:cashRegisterFileQuery>
    </base:QueryCashRegisterFileRequest>
  </soapenv:Body>
</soapenv:Envelope>
'''




body = soap_body.encode('utf-8')


# Send the SOAP request
response = requests.post(
    url,
    data=body
)

# Print the response
print(response.status_code)