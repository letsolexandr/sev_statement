from django.core.validators import RegexValidator,FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from .cryptoserver.api import CryptoClient

__all__ = ['phone_validator']

phone_validator = RegexValidator(
    regex=r'^\+?3?8?(0\d{9})$',
    message=_("Phone number must be entered in the format '+123456789'. Up to 15 digits allowed.")
)


def sign_validator(sign_data=None, cert_path=None):
    crypto_client = CryptoClient()
    result = crypto_client.verify_data(sign_data=sign_data, cert_path=cert_path)
    if result.get('code') not in (0,):
        raise ValidationError(result.get('code_message'))
