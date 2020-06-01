import zeep
import base64
import logging

from .settings import BASE_URL, MESSAGE_CODES, UACS_SUCCESS

logger = logging.getLogger(__name__)


class CryptoClient(object):
    def __init__(self):
        self.client = zeep.Client(wsdl=BASE_URL)

    def data_to_base_64(self, data_path):
        if hasattr(data_path, 'read'):
            data_b = data_path.read()
            return base64.b64encode(data_b)
        else:
            with open(data_path, 'rb') as data:
                data_b = data.read()
                return base64.b64encode(data_b)

    def base_64_to_data(self, data):
        return base64.b64decode(data)

    def verify_data_data_path(self, data_path=None, cert_path=None, sign_data=None):
        if cert_path:
            cert64 = self.data_to_base_64(cert_path)
        else:
            cert64 = None
        sign_data64 = sign_data
        data_64 = self.data_to_base_64(data_path)
        result = self.client.service.verify(data=sign_data64, dataExt=data_64, cert=cert64)
        code_message = MESSAGE_CODES.get(result.code)
        str_result = str(result).replace("'",'"').replace('\n','')
        ret_result = eval(str_result)
        ret_result.update({'code_message': code_message})
        return ret_result

    def __verify_data(self, cert_path=None, sign_data=None):
        cert64 = self.data_to_base_64(cert_path)
        sign_data64 = self.data_to_base_64(sign_data)
        result = self.client.service.verify(data=sign_data64, cert=cert64)
        return result

    def verify_data(self, data_path=None, cert_path=None, sign_data=None):
        if data_path:
            result = self.verify_data_data_path(data_path=data_path, cert_path=cert_path, sign_data=sign_data)
        else:
            result = self.__verify_data(cert_path=cert_path, sign_data=sign_data)
        code_message = MESSAGE_CODES.get(result.code)
        ret_result = {'code': result.code,
                      'code_message': code_message,
                      'message': result.message,
                      'data': result.data,
                      'cert': result.cert}
        return ret_result

    def encrypt_directly(self, data_path=None, cert_path=None):
        cert64 = self.data_to_base_64(cert_path)
        data_64 = self.data_to_base_64(data_path)
        result = self.client.service.encrypt(data=data_64, recipient=cert64)
        return result

    def encrypt_by_crypto_server(self, data_path=None):
        data_64 = self.data_to_base_64(data_path)
        result = self.client.service.encrypt(data=data_64)
        return result

    def encrypt(self, data_path=None, cert_path=None):
        if cert_path:
            result = self.encrypt_directly(data_path, cert_path)
        else:
            result = self.encrypt_by_crypto_server(data_path)
        code_message = MESSAGE_CODES.get(result.code)
        ret_result = {'code': result.code,
                      'code_message': code_message,
                      'message': result.message,
                      'data': result.data,
                      'cert': result.cert}
        return ret_result

    def decrypt(self, data_64=None, cert_path=None):
        if cert_path:
            result = self.decrypt_directly(data_64, cert_path)
        else:
            result = self.decrypt_by_server(data_64)
        code_message = MESSAGE_CODES.get(result.code)
        ret_result = {'code': result.code,
                      'code_message': code_message,
                      'message': result.message,
                      'data': result.data,
                      'cert': result.cert}
        return ret_result

    def decrypt_directly(self, data_64=None, cert_path=None):
        cert64 = self.data_to_base_64(cert_path)
        result = self.client.service.decrypt(data=data_64, originator=cert64)
        return result

    def decrypt_by_server(self, data_64=None):
        result = self.client.service.decrypt(data=data_64)
        return result
