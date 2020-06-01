import zeep
import base64

BASE_URL = "http://10.0.40.121:8080/Server/UACryptoSign?wsdl"

UACS_SUCCESS = 0
UACS_SERVER_INTERNAL_ERROR = 1
UACS_CRYPTO_ERROR = 2
UACS_INVALID_PARAM = 3
UACS_DATA_NOT_FOUND = 4
UACS_DATA_DONT_MATCH = 5
UACS_CERTIFICATE_NOT_FOUND = 6
UACS_CERTIFICATE_DONT_MATCH = 7
UACS_CERTIFICATE_REVOKED = 8
UACS_WRONG_RECIPIENT = 9

MESSAGE_CODES = {UACS_SUCCESS: """Успішно. """,
                 UACS_SERVER_INTERNAL_ERROR: """Внутрішня помилка Серверу.""",
                 UACS_CRYPTO_ERROR: """Помилка виконання криптографічної операції. """,
                 UACS_INVALID_PARAM: """Невірне значення вхідного параметру або відсутність обов’язкового параметру функції.""",
                 UACS_DATA_NOT_FOUND: """Помилка обробки повідомлення з ЕЦП. До функції не передані підписані дані, при цьому повідомлення з ЕЦП не містить підписаних даних. """,
                 UACS_DATA_DONT_MATCH: """Помилка обробки повідомлення з ЕЦП. До функції передані підписані дані, повідомлення з ЕЦП містить підписані даних та ці дані не співпадають.""",
                 UACS_CERTIFICATE_NOT_FOUND: """Помилка обробки повідомлення з ЕЦП. Не знайдено сертифікат підписувача.""",
                 UACS_CERTIFICATE_DONT_MATCH: """Помилка обробки повідомлення з ЕЦП. Переданий до функції сертифікат підписувача не відповідає сертифікату, з використанням якого обчислений ЕЦП. Помилка обробки повідомлення з зашифрованими даними. Переданий до функції сертифікат отримувача не відповідає сертифікату, з використанням якого дані зашифровані.""",
                 UACS_CERTIFICATE_REVOKED: """Помилка обробки повідомлення з ЕЦП. Сертифікат підписувача відкликаний, строк чинності сертифіката не почався або завершений. """,
                 UACS_WRONG_RECIPIENT: """Помилка обробки повідомлення з зашифрованими даними. Сервер не є отримувачем повідомлення. """}

message = b'432423423423'
message64 = base64.b64encode(message)
print(message64)
cert = open(u"D:\DOC\Тестова Юридична Особа.cer", 'rb').read()
cert64 = base64.b64encode(cert)
key =  open(u"D:\DOC\Key-6.dat", 'rb').read()
key64 = base64.b64encode(key)

print(cert64)

signed_data = open(u"D:\DOC\mnj_2016_6(1)__23.pdf.p7s", 'rb').read()
signed_data64 = base64.b64encode(signed_data)

data_ext = open(u"D:\DOC\mnj_2016_6(1)__23.pdf", 'rb').read()
data_ext64 = base64.b64encode(data_ext)

client = zeep.Client(wsdl=BASE_URL)
print(dir(client.service))

print("======== signAttach ===========\n")
result_sign_attach = client.service.signAttach(message64)
print(result_sign_attach)
print(MESSAGE_CODES.get(result_sign_attach.code))

print("======== verifyAttach ===========\n")
result = client.service.verifyAttach(result_sign_attach.data)
print(result)
print(MESSAGE_CODES.get(result.code))

print("======== Direct encrypt ===========\n")
result = client.service.encrypt(data=message64, recipient=cert64)
print(result)
print(MESSAGE_CODES.get(result.code))

print("======== Direct decrypt ===========\n")
result = client.service.decrypt(data=result.data, originator=key64)
print(result)
print(MESSAGE_CODES.get(result.code))

print("======== IIT envelope ===========\n")
result = client.service.verify(data=signed_data64, dataExt=data_ext64, cert=cert64)
print(result)
print(MESSAGE_CODES.get(result.code))
