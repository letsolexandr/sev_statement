import unittest
import os
from .api import CryptoClient
from .settings import UACS_SUCCESS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DATA_PATH = os.path.join(BASE_DIR, 'test_data')


class TestCryptoMethods(unittest.TestCase):
    def test_init_crypto_client(self):
        ##print(self._testMethodName)
        test_crypto = CryptoClient()
        self.crypto_client = test_crypto
        self.assertTrue(True)

    def test_verify_data(self):
        test_crypto = CryptoClient()
        file_path = os.path.join(TEST_DATA_PATH, 'mnj_2016_6(1)__23.pdf')
        sign_file_path = os.path.join(TEST_DATA_PATH, 'mnj_2016_6(1)__23.pdf.p7s')
        cert_path = os.path.join(TEST_DATA_PATH, 'TEST_CERT.cer')
        result = test_crypto.verify_data(file_path, cert_path, sign_file_path)
        self.assertTrue(result.get('code') == UACS_SUCCESS)

    def test_encrypt_data(self):
        self.encrypt_data = None
        test_crypto = CryptoClient()
        file_path = os.path.join(TEST_DATA_PATH, 'mnj_2016_6(1)__23.pdf')
        cert_path = os.path.join(TEST_DATA_PATH, 'TEST_CERT.cer')
        result = test_crypto.encrypt(file_path, cert_path)
        self.assertTrue(result.get('code') == UACS_SUCCESS)
        self.assertTrue(result.get('data'))
        self.encrypt_data = result.get('data')


    def test_decrypt_data(self):
        test_crypto = CryptoClient()
        cert_path = os.path.join(TEST_DATA_PATH, 'TEST_CERT.cer')
        self.test_encrypt_data()
        result = test_crypto.decrypt(self.encrypt_data, cert_path)
        print(result.get('code'))
        ##self.assertTrue(result.get('code') == UACS_SUCCESS)


if __name__ == '__main__':
    unittest.main(module='__main__')
