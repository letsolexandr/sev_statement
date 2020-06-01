from l_core.models import CoreBase
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.validators import FileExtensionValidator

from l_core.models import Counter
from l_core.utilits.finance import get_pdv, get_without_pdw, calculate_pdv

import os
import docxtpl
from django.utils.crypto import get_random_string
from dict_register.models import TemplateDocument
from django.conf import settings
from l_core.utilits.converter import LibreOfficeConverter
from django.utils.timezone import now
from datetime import datetime, timedelta
import base64
from dict_register.models import Product, Subscription

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL

STATEMENT_STATUS = (('1', 'Нова'),
                    ('2', 'Відпрацьована'),
                    ('3', 'Узгодження реквізитів'),
                    ('4', 'Відправлено на підпис конрагенту'),
                    ('5', 'Відмовлено'),
                    ('6', 'Договір підписано'),
                    ('7', 'Прострочена'),
                    )
## Кількість днів на відправку договору контрагенту
CONTROL_PERIOD = 14


class Integration(models.Model):
    """Послуги """
    ##################################################################
    INT_TARIFF_PLAN_COST = {200: 325, 250: 439, 500: 833, 2500: 1270.83}
    INT_INTEGRATION_CHOICES = [(200, 'Інтеграція 200'),
                               (250, 'Інтеграція 250'),
                               (500, 'Інтеграція 500'),
                               (1000, 'Інтеграція 1000'),
                               (2500, 'Інтеграція 2500')]
    ##################################################################

    int_integration_type = models.ForeignKey('dict_register.Subscription', on_delete=models.CASCADE,
                                             related_name='integration_type_subscription',
                                             verbose_name='Тарифний план', null=True)

    int_access_to_SEV_OVV = models.BooleanField(default=True,
                                                verbose_name='Надання доступу шляхом підключення СЕД до СЕВ ОВВ')

    class Meta:
        abstract = True
        managed = False
        verbose_name = u'Вартість тарифного плану послуги'
        verbose_name_plural = u'Вартість тарифних планів послуг'


class Web(models.Model):
    """ Додаткові послуги """
    ##############################################
    WEB_TARIFF_PLAN_COST = {50: 215.00, 200: 303.00}
    WEB_TARIFF_PLAN_CHOICES = [(50, 'Веб-50'), (200, 'Веб-200')]
    WEB_ACCESS_COST = 60
    CRYPTO_AUTOGRAPH_COST = 459.28
    VPN_ON_PC = 459.28
    VPN_ON_SERVER = 918.54
    STUDY_SEV_OVV = 1224.72
    SEMINAR_SEV_OVV = 2360.65
    ##############################################

    web_tariff_plan = models.ForeignKey('dict_register.Subscription', on_delete=models.CASCADE,
                                        verbose_name='Тарифний план', related_name='web_tariff_plan_subscription',
                                        null=True)

    web_access_count = models.IntegerField(default=0,
                                           verbose_name='Надання веб-доступу (за кожного додаткового користувача) на місяць')
    web_service_install_crypto_autograph = models.BooleanField(default=False,
                                                               verbose_name='Послуги по установці на ПК користувача засобу криптографічного захисту інформації "Крипто автограф"')
    crypto_autograph_count = models.IntegerField(default=0, null=True, verbose_name="Кількість крипто-автографу")
    web_service_install_cisco_vpn_onPC = models.BooleanField(default=False,
                                                             verbose_name='Послуги по установці на ПК користувача програмного криптографічного захисту інформації CISCO U VPN-ZAS')
    install_cisco_vpn_onPC_count = models.IntegerField(default=0, null=True, verbose_name="Кількість VPN")
    web_service_install_cisco_vpn_onServer = models.BooleanField(default=False,
                                                                 verbose_name='Послуги по установці на серверну частину клієнта програмного криптографічного захисту інформації CISCO U VPN-ZAS')
    web_service_study_SEV_OVV = models.BooleanField(default=False,
                                                    verbose_name='Послуги по навчанню на робочому місці користувача системи електронної взаємодії органів виконавчої влади версія 2.0')
    web_seminar_use_IT_in_SEV_OVV = models.BooleanField(default=False,
                                                        verbose_name='Навчально-консультаційний семінар-практикум «Застосування інформаційних технологій в роботі СЕВ ОВВ» на одну особу')

    class Meta:
        abstract = True
        managed = False
        verbose_name = u'Вартість тарифного плану додаткових послуг'
        verbose_name_plural = u'Вартість тарифних планів додаткових послуг'


def calc_control_data():
    return now() + timedelta(days=CONTROL_PERIOD)


class AdditionalService(CoreBase):
    statement = models.ForeignKey('SEDStatement', on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    count = models.IntegerField(default=1)


class SEDStatement(CoreBase, Integration, Web):
    """Заявки """
    STATEMENT_TYPE = (('integration', 'Інтеграція'), ('web', 'Веб-доступ'))
    statement_date = models.DateField(verbose_name="Дата заявки", default=now)
    control_date = models.DateField(null=True, default=calc_control_data, verbose_name="Дата заявки")
    reg_number = models.TextField(default='-', verbose_name="Номер заявки")
    ecp_certificate = models.FileField(null=True, verbose_name="ЕЦП відкритий ключ")
    statement_type = models.CharField(max_length=50, choices=STATEMENT_TYPE,
                                      verbose_name='Тип заявки')
    status = models.CharField(max_length=50, default='1', choices=STATEMENT_STATUS, verbose_name='Статус заявки')
    contractor = models.ForeignKey('l_core.CoreOrganization', related_name='%(class)s_contractor',
                                   on_delete=models.PROTECT, verbose_name="Контрагент")
    is_send_to_technician = models.BooleanField(default=False, verbose_name='Направлено в технічний відділ?')
    is_contractor_connected = models.BooleanField(default=False, verbose_name='Контрагента підключено?')
    statement_doc = models.FileField(null=True, verbose_name="Заява на підключення")
    statement_doc_sign = models.FileField(null=True, verbose_name="Підпис")
    verified = models.BooleanField(default=False, verbose_name='Підпис заяви перевірено?')
    sign_is_valid = models.BooleanField(default=False, verbose_name='Підпис заяви валідний?')
    sign_b64 = models.TextField(null=True)
    verify_result = JSONField(null=True)
    statute_copy = models.FileField(null=True, verbose_name="Статутні документи",
                                    validators=[
                                        FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg'])])
    all_data = JSONField(null=True)
    note = models.TextField(verbose_name='Примітка', null=True)

    class Meta:
        verbose_name_plural = u'Заявки на підключення до СЕВСЕД'
        verbose_name = u'Заявка на підключення до СЕВСЕД'
        ordering = ["id", ]

    def __str__(self):
        return self.__unicode__()

    def save(self, *args, **kwargs):
        if not self.id and not self.reg_number:
            self.set_reg_number()
        super(SEDStatement, self).save()

    def set_reg_number(self):
        self.reg_number = Counter.next_id('statement_sed_statement')

    def get_price(self):
        if self.statement_type == "integration":
            return self.INT_TARIFF_PLAN_COST[self.int_integration_type]
        elif self.statement_type == "web":
            cost = self.web_tariff_plan.price_pdv
            cost += (float(self.web_access_count) * float(self.WEB_ACCESS_COST))
            return cost

    def get_tariff_plan(self, params):

        if self.statement_type == "integration":
            count = 1
            return {"service": self.int_integration_type.name, "count": count,
                    "total_cost": self.int_integration_type.price * count}
        elif self.statement_type == "web":
            service = Subscription.objects.get(pk=6)  ## Підключення додаткового користувача
            user_count = len(params.get('users'))

            count = 0 if user_count == 1 else user_count - 1
            additional_users_price = (service.price * count)

            return {"service": self.web_tariff_plan.name, "count": count,
                    "total_cost": additional_users_price + self.web_tariff_plan.price}

    def get_connection(self, params=None):
        if self.statement_type == "integration":
            return Product.objects.get(pk=16)
        elif self.statement_type == "web":
            return Product.objects.get(pk=14)

    def get_additional_services(self, params, to_generate_contract=None):
        result = []
        if self.web_access_count > 1:
            count = self.web_access_count - 1
            additional_user_service = Product.objects.get(pk=15)
            data = {"name": additional_user_service.name,
                    "product_price": additional_user_service.price,
                    "count": count,
                    "price": additional_user_service.price * count}
            if (to_generate_contract):
                data["service"] = additional_user_service
            result.append(data)

        for service in self.additionalservice_set.all():
            data = {"name": service.product.name,
                    "product_price": service.product.price,
                    "count": service.count,
                    "price": service.product.price * service.count}

            if (to_generate_contract):
                data["service"] = service.product
            result.append(data)

        return result

    def notify_contractor(self):
        # TODO Зробити відправку листа на пошту контрагента
        # from django.core.mail import EmailMultiAlternatives
        #
        # subject, from_email, to = 'hello', 'from@example.com', 'to@example.com'
        # text_content = 'This is an important message.'
        # html_content = '<p>This is an <strong>important</strong> message.</p>'
        # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        # msg.attach_alternative(html_content, "text/html")
        # msg.send()
        pass

    def get_initials_from_name(self, full_name):
        try:
            ##full_name = 'ПЕТРЕНКО ПЕТРО ПЕТРОВИЧ'
            m = full_name.lstrip()
            l = m.split(' ')
            i3 = l[0]
            i1 = l[1].upper()[0] + '.'
            i2 = l[2].upper()[0] + '.'
            f_string = f'{i3} {i1}{i2}'
            ##f_string = 'ПЕТРОВИЧ П.П.'
            return f_string
        except:
            return None

    def get_data(self, params):
        data = params.copy()
        data['connection'] = self.get_connection(params)
        data['tariff_plan'] = self.get_tariff_plan(params)
        data['additional_services'] = self.get_additional_services(params)
        data['statement_date'] = now().strftime('%d.%m.%Y')
        data['subject']['main_unit_initials'] = self.get_initials_from_name(data['subject']['main_unit'])
        return data

    def get_tariff_plan_name(self):
        if self.statement_type == "integration":
            return self.int_integration_type.name
        elif self.statement_type == "web":
            return self.web_tariff_plan.name
        else:
            raise Exception('"statement_type" is required!!')

    @classmethod
    def create_pdf_statement(cls, params, obj=None):
        doc_path = cls.generate_docx_statement(params, obj=obj)
        res = cls.convert_docx_to_pdf(doc_path, params, obj=obj)
        return res

    @classmethod
    def convert_docx_to_pdf(cls, source, params, obj=None):
        """ Return *.pdf path from MEDIA_ROOT """
        upload_to = f'uploads/statement/pdf/{params.get("edrpou") or params.get("ipn")}'

        out_path = os.path.join(MEDIA_ROOT, upload_to)
        filename = os.path.basename(source).replace('.docx', '.pdf')
        ret = os.path.join(MEDIA_URL, upload_to, filename)
        out_file = os.path.join(out_path, filename)
        LibreOfficeConverter.convert_to_pdf(source, out_file)
        if obj:
            obj.statement_doc = os.path.join(upload_to, filename)
            obj.save()
        return ret

    def save_ecp_certificate(self, cert_data, edrpou):
        filename = f'{edrpou}.cer'
        upload_to = f'uploads/cert/{edrpou}'
        out_path = os.path.join(MEDIA_ROOT, upload_to)
        out_file = os.path.join(out_path, filename)
        if not os.path.exists(out_path):
            os.makedirs(out_path)
        with open(out_file, 'wb') as cert:
            cert.write(cert_data)

        return os.path.join(upload_to, filename)

    def get_doc_b64(self):
        with open(self.statement_doc.path, 'rb') as data:
            data_b = data.read()
            return base64.b64encode(data_b)

    @classmethod
    def generate_docx_statement(cls, params, obj=None):
        template_obj = TemplateDocument.objects.get(related_model_name='sev_web_template')
        docx_template = template_obj.template_file.path
        doc = docxtpl.DocxTemplate(docx_template)
        upload_to = f'uploads/statement/docx/{params.get("edrpou") or params.get("ipn")}'
        base_dir = os.path.join(MEDIA_ROOT, upload_to)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        filename = get_random_string(length=32) + '.docx'
        out_path = os.path.join(base_dir, filename)
        data = params
        if obj:
            data = obj.get_data(params)
        doc.render(data)
        doc.save(out_path)
        return out_path

    def __unicode__(self):
        return 'Заявка №{0}'.format(self.reg_number or '-')
