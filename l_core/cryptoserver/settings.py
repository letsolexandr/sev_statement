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

CRYPTO_SERVER_NAME = '(Модуль криптографічного захисту).'

MESSAGE_CODES = {UACS_SUCCESS: """Успішно."""+CRYPTO_SERVER_NAME,
                 UACS_SERVER_INTERNAL_ERROR: """Внутрішня помилка Серверу."""+CRYPTO_SERVER_NAME,
                 UACS_CRYPTO_ERROR: """Помилка виконання криптографічної операції. """+CRYPTO_SERVER_NAME,
                 UACS_INVALID_PARAM: """Невірне значення вхідного параметру або відсутність обов’язкового параметру функції."""+CRYPTO_SERVER_NAME,
                 UACS_DATA_NOT_FOUND: """Помилка обробки повідомлення з ЕЦП. До функції не передані підписані дані, при цьому повідомлення з ЕЦП не містить підписаних даних. """+CRYPTO_SERVER_NAME,
                 UACS_DATA_DONT_MATCH: """Помилка обробки повідомлення з ЕЦП. До функції передані підписані дані, повідомлення з ЕЦП містить підписані даних та ці дані не співпадають."""+CRYPTO_SERVER_NAME,
                 UACS_CERTIFICATE_NOT_FOUND: """Помилка обробки повідомлення з ЕЦП. Не знайдено сертифікат підписувача."""+CRYPTO_SERVER_NAME,
                 UACS_CERTIFICATE_DONT_MATCH: """Помилка обробки повідомлення з ЕЦП. Переданий до функції сертифікат підписувача не відповідає сертифікату, з використанням якого обчислений ЕЦП. Помилка обробки повідомлення з зашифрованими даними. Переданий до функції сертифікат отримувача не відповідає сертифікату, з використанням якого дані зашифровані."""+CRYPTO_SERVER_NAME,
                 UACS_CERTIFICATE_REVOKED: """Помилка обробки повідомлення з ЕЦП. Сертифікат підписувача відкликаний, строк чинності сертифіката не почався або завершений. """+CRYPTO_SERVER_NAME,
                 UACS_WRONG_RECIPIENT: """Помилка обробки повідомлення з зашифрованими даними. Сервер не є отримувачем повідомлення. """+CRYPTO_SERVER_NAME}


