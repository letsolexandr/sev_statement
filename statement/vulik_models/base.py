from django.db import models

from l_core.models import CoreBase
from django.core.validators import MinLengthValidator, FileExtensionValidator

from l_core.validators import phone_validator
STATEMENT_STATUS = (('1', 'Нова'),
                    ('2', 'Відпрацьована'),
                    ('3', 'Узгодження реквізитів'),
                    ('4', 'Відправлено на підпис конрагенту'),
                    ('5', 'Відмовлено'),
                    ('6', 'Закрита'),
                    ('7', 'Прострочена'),
                    )

class ConnectionCNAPStatement(CoreBase):
    """ Заявка на підключення до Системи ЦНАП """
    CNAP_USER = (('1', 'Працівник ЦНАП'),
                 ('2', """Працівник Державного підприємства "Державний центр інформаційних ресурсів 
України"""""),)

    reg_number = models.TextField(default='-', verbose_name="Номер заявки")
    name_manage_company = models.TextField(validators=[MinLengthValidator(5)],
                                           verbose_name="повне найменування органу, що прийняв рішення про створення ЦНАП")
    edrpou_manage_company = models.CharField(max_length=10, validators=[MinLengthValidator(10)],
                                             verbose_name="ЄДРПОУ органу, що прийняв рішення про створення ЦНАП")
    cnap_user = models.CharField(max_length=1, choices=CNAP_USER, verbose_name="Додати користувача")

    first_name = models.CharField(null=True, validators=[MinLengthValidator(3)], max_length=25,
                                  verbose_name="Ім'я працівника ЦНАП")
    last_name = models.CharField(null=True, validators=[MinLengthValidator(3)], max_length=25,
                                 verbose_name="Прізвище працівника ЦНАП")
    middle_name = models.CharField(null=True, validators=[MinLengthValidator(3)], max_length=25,
                                   verbose_name="По батькові працівника ЦНАП")
    phone_integrator = models.CharField(null=True, max_length=16, validators=[phone_validator, MinLengthValidator(10)],
                                        verbose_name="телефон працівника ЦНАП")
    mail_integrator = models.EmailField(null=True, max_length=64, verbose_name="електронна пошта працівника ЦНАП")
    short_name_cnap = models.CharField(max_length=256, validators=[MinLengthValidator(3)],
                                       verbose_name="скорочене найменування ЦНАП")
    full_name_cnap = models.CharField(max_length=256, validators=[MinLengthValidator(5)],
                                      verbose_name="Повне найменування ЦНАП")
    address_cnap = models.CharField(max_length=256, validators=[MinLengthValidator(5)], verbose_name="адреса ЦНАП")

    phone_cnap = models.CharField(max_length=16, validators=[phone_validator, MinLengthValidator(10)],
                                  verbose_name="телефон ЦНАП")
    mail_cnap = models.EmailField(verbose_name="електронна пошта ЦНАП")

    signet_doc = models.FileField(verbose_name="Підписана заява",
                                  help_text="""Заява підписана за ЕЦП. Файл з розширенням p7s""",
                                  validators=[FileExtensionValidator(allowed_extensions=['p7s'])])
    ecp_certificate = models.FileField(verbose_name="ЕЦП відкритий ключ",
                                       help_text="""Завантажуються цертифікат відкритиго ключа електронного цифрового підпису""",
                                       validators=[FileExtensionValidator(allowed_extensions=['cer\"', 'cer'])]
                                       )
    status = models.CharField(max_length=50, default='1', choices=STATEMENT_STATUS,
                              verbose_name='Статус заявки')

    class Meta:
        abstract=True