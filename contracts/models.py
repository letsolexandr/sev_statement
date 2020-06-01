from datetime import date
from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
from typing import List
from django.core.files.uploadedfile import InMemoryUploadedFile
##import json
import os
import docxtpl
from babel.dates import format_datetime
from num2words import num2words

from django.db import models
from django.db.models import Sum
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from l_core.models import CoreBase, CoreOrganization
from l_core.utilits.converter import LibreOfficeConverter

from l_core.utilits.month import LOCAL_MONTH
from l_core.models import Counter
from l_core.utilits.finance import get_pdv, calculate_pdv, get_without_pdw
from contracts.model_details.PaymentUpload import ImportPayment
from statement.models import SEDStatement

from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT


import logging

logger = logging.getLogger(__name__)

# Дата нарахування буде відображатись в рахунку на оплату
CHARGING_DAY = 20


class Contract(CoreBase):
    CONTRACT_STATUS = [
        ['future', 'Укладається'],
        ['actual', 'Дійсний'],
        ['archive', 'Архівний'],
        ['rejected', 'Не заключений']
    ]
    parent_element = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                       verbose_name="Батьківський елемент")
    statement = models.ForeignKey('statement.SEDStatement', on_delete=models.SET_NULL, null=True, blank=True,
                                  verbose_name="Заявка")
    number_contract = models.TextField(max_length=50, verbose_name="№ Договору", null=True)
    start_date = models.DateField(verbose_name="Дата заключення договору")
    start_of_contract = models.DateField(verbose_name="Дата початку дії договору")
    start_payment = models.DateField(null=True, blank=True, verbose_name="Дата початку оплати")
    start_accrual = models.DateField(null=True, blank=True, verbose_name="Дата початку нарахувань")
    subject_contract = models.TextField(max_length=500, null=True, verbose_name="Предмет договору")
    contractor = models.ForeignKey('l_core.CoreOrganization', related_name='%(class)s_contractor', null=True,
                                   blank=True,
                                   on_delete=models.PROTECT, verbose_name="Контрагент")
    price_contract = models.FloatField(default=0, verbose_name="Ціна договору")
    price_contract_by_month = models.FloatField(default=0, verbose_name="Ціна договору за місяць")
    contract_time = models.IntegerField(verbose_name="Строк дії договору", null=True, blank=True)
    one_time_service = models.BooleanField(verbose_name="Одноразова послуга/купівля", default=False)
    expiration_date = models.DateField(verbose_name="Дата закінчення")
    copy_contract = models.FileField(upload_to='uploads/copy_contract/%Y/%m/%d/', null=True,
                                     verbose_name="Копія договору")
    contract_docx = models.FileField(upload_to='uploads/contract_docx/%Y/%m/%d/', null=True,
                                     verbose_name="Проект договору")
    status = models.CharField(max_length=20, choices=CONTRACT_STATUS, default='future', verbose_name="Статус")
    automatic_number_gen = models.BooleanField(default=False, verbose_name="Сформувати номер автоматично?")

    class Meta:
        verbose_name_plural = u'Договори'
        verbose_name = u'Договір'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0}'.format(self.number_contract or '-')

    def save(self, *args, **kwargs):
        if not self.id:
            self.contract_time = self.get_contract_time()
            self.set_organization_from_statement()
            self.set_tariff_plan_name_from_statement()
            self.set_number_contract()
            self.set_start_accrual()
        super(Contract, self).save(*args, **kwargs)

        ##self.set_details_from_statement()
        ##self.set_price_from_details()

    def set_organization_from_statement(self):
        """ Якщо організація при створенні договору не вказана, отримуємо її з Завки"""
        if not self.contractor and self.statement:
            self.contractor = self.statement.contractor

    def set_number_contract(self):
        """Автоматично встановлює номер нового договору якщо це необхідно"""
        if not self.id and self.automatic_number_gen:
            n = Counter.next_id('contracts_contract')
            ## 2/2019/K
            number_contract = f"{n}/{self.start_date.year}/{self.contractor.bank}"
            self.number_contract = number_contract

    def set_tariff_plan_name_from_statement(self):
        """"Отримати тарифний план з заявки, якщо вона існує"""
        if self.statement:
            self.subject_contract = self.statement.get_tariff_plan_name()
            return self.subject_contract

    def set_details_from_statement(self):
        """Отрмати деталі заявки - список послуг та таривний план"""
        ## Обслуговування
        from dict_register.models import Subscription##, Product
        ## tarrif plan "web"
        if self.statement.statement_type == "web":
            ## Додаємо  оплату за підключення
            ##TODO - знайти веселіший спосіб знаходити обєкти (не по id)
            connection_payment = self.statement.get_connection()
            ContractProducts.objects.create(contract=self, product=connection_payment, count=1,
                                            price=connection_payment.price,
                                            total_price=connection_payment.price,
                                            pdv=connection_payment.pdv,
                                            total_price_pdv=1 * connection_payment.price_pdv)
            #####################################################################################
            ## Отримуємо тарифний план з заявки
            product = self.statement.web_tariff_plan
            count = 1
            ContractSubscription.objects.create(contract=self, product=product, start_period=self.start_accrual,
                                                end_period=self.expiration_date, count=count, price=product.price,
                                                total_price=count * product.price,
                                                pdv=product.pdv,
                                                total_price_pdv=count * product.price_pdv, charging_day=CHARGING_DAY)
            #####################################################################################
            ## Прописуємо дадаткових користувачів
            users_count = len(self.statement.all_data.get('users'))
            ## один користувач входить в абонплату, визначаємо кількість додаткових
            add_users_count = users_count - 1
            ## Оплата за підключення додаткового користувача
            product = Subscription.objects.get(pk=6)
            if add_users_count > 0:
                ContractSubscription.objects.create(contract=self, product=product, start_period=self.start_accrual,
                                                    end_period=self.expiration_date, count=add_users_count,
                                                    price=product.price, charging_day=CHARGING_DAY,
                                                    total_price=add_users_count * product.price,
                                                    pdv=product.pdv,
                                                    total_price_pdv=add_users_count * product.price_pdv)

        ## tarrif plan "integration"
        if self.statement.statement_type == "integration":
            ## Додати оплату за підключення#####################################################
            connection_payment = self.statement.get_connection()  ## для інтеграції
            ContractProducts.objects.create(contract=self, product=connection_payment, count=1,
                                            price=connection_payment.price,
                                            total_price=connection_payment.price,
                                            pdv=connection_payment.pdv,
                                            total_price_pdv=1 * connection_payment.price_pdv)
            #####################################################################################
            ###Тарифний план##############################
            product = self.statement.int_integration_type
            count = 1
            ContractSubscription.objects.create(contract=self, product=product, start_period=self.start_accrual,
                                                end_period=self.expiration_date, count=count, price=product.price,
                                                total_price=count * product.price,
                                                pdv=product.pdv,
                                                total_price_pdv=count * product.price_pdv, charging_day=CHARGING_DAY)
            #########################################################################################################

        ## Додаємо додаткові послуги
        statement:SEDStatement = self.statement
        additional_services =statement.get_additional_services(None, to_generate_contract=True)
        for service in additional_services:
            print(service)
            ContractProducts.objects.create(contract=self,
                                            product=service.get("service"),
                                            count=service.get("count"),
                                            price=service.get("service").price,
                                            total_price=service.get("count") * service.get("service").price,
                                            pdv=service.get("service").pdv,
                                            total_price_pdv=service.get("count") * service.get(
                                                "service").price_pdv)

    def set_price_from_details(self):
        ## Зараз не використовується
        total_price_subscription_pdv = \
            ContractSubscription.objects.filter(contract=self).aggregate(Sum('total_price_pdv'))[
                'total_price_pdv__sum'] or 0
        total_price_products_pdv = ContractProducts.objects.filter(contract=self).aggregate(Sum('total_price_pdv'))[
                                       'total_price_pdv__sum'] or 0
        ## Кількість місяців в періоді платежів
        month_count = len(self.get_pay_periods())
        self.price_contract = (month_count * total_price_subscription_pdv) + total_price_products_pdv
        self.price_contract_by_month = total_price_subscription_pdv
        self.save()

    def get_contract_subscription_price(self):
        total_price_pdv = ContractSubscription.objects.filter(contract=self).aggregate(Sum('total_price_pdv'))[
                              'total_price_pdv__sum'] or 0
        return total_price_pdv

    def get_contract_product_price(self):
        total_price_pdv = ContractProducts.objects.filter(contract=self).aggregate(Sum('total_price_pdv'))[
                              'total_price_pdv__sum'] or 0
        return total_price_pdv

    def set_start_accrual(self):
        """Якщо початок договору пізніше 10-го числа поточного місяця,
        то початок нарахувань з 1-го числа настпного місяця, якшо менше то з 1-го поточного"""
        if self.start_date.day > 10:
            next_month = datetime(self.start_date.year, self.start_date.month, 1) + relativedelta(months=+1)
            self.start_accrual = next_month
        else:
            self.start_accrual = self.start_date

    def get_contract_time(self):
        if self.expiration_date and self.start_accrual:
            return (self.expiration_date - self.start_accrual).days
        else:
            return 0

    @classmethod
    def refresh_total_balance(cls):
        contracts = Contract.objects.all()
        ##contracts = Contract.objects.values('country__name').annotate(Sum('population'))
        for contract in contracts:
            contract.save()
        return contracts.count()

    @classmethod
    def calculate_accruals(cls, start_date=None, end_date=None, create_pdf=None, is_comercial=None, is_budget=None):
        contracts = cls.objects.filter(expiration_date__gte=(end_date or date.today()))
        result = []
        for contract in contracts:
            res = RegisterAccrual.calculate_accruals(contract=contract, start_date=start_date, end_date=end_date)
            result.append(res)
        return result

    def calculate_accrual(self):
        res = RegisterAccrual.calculate_accruals(contract=self)
        return res

    def get_initials_from_name(self, full_name):
        try:
            ##full_name = 'ПЕТРЕНКО ПЕТРО ПЕТРОВИЧ'
            m = full_name.lstrip()
            l = m.split(' ')
            i3 = l[0]
            i1 = l[1].upper()[0] + '.'
            i2 = l[2].upper()[0] + '.'
            f_string = f'{i1}{i2}{i3}'
            ##f_string = 'П.П. ПЕТРОВИЧ'
            return f_string
        except:
            return None

    def set_docx(self):
        if not self.contract_docx:
            self.contract_docx = self.generate_doc()

    def get_doc_data(self):
        from dict_register.models import Subscription, Product
        data = {}
        stage_property_q = StageProperty.objects.filter(contract=self)
        if stage_property_q.count() > 0:
            stage_property = stage_property_q[0]
            stage_property_data = {'name': stage_property.name,
                                   'address': stage_property.address,
                                   'main_unit_state': stage_property.main_unit_state,
                                   'main_unit': stage_property.main_unit,
                                   'main_unit_initials': self.get_initials_from_name(stage_property.main_unit),
                                   'bank_name': stage_property.bank_name,
                                   'settlement_account': stage_property.settlement_account,
                                   'certificate_number': stage_property.certificate_number,
                                   'org_reason': stage_property.work_reason,
                                   'ipn': stage_property.ipn,
                                   'mfo': stage_property.mfo,
                                   'edrpou': stage_property.edrpou,
                                   'phone': stage_property.phone,
                                   'email': stage_property.email}
        else:
            stage_property_data = None
        data['statement_name'] = self.subject_contract
        data['stage_property_data'] = stage_property_data
        data['start_date'] = self.start_date
        data['end_date'] = self.expiration_date
        local_contract_date = format_datetime(self.start_date, "«d» MMMM Y", locale='uk_UA')
        data['local_contract_date'] = local_contract_date

        local_contract_end_date = format_datetime(self.expiration_date, "«d» MMMM Y", locale='uk_UA')
        data['local_contract_end_date'] = local_contract_end_date

        data['number_contract'] = self.number_contract

        data['price_by_month'] = self.price_contract_by_month
        data['pdv_by_month'] = get_pdv(self.price_contract_by_month)
        data['price_by_month_no_pdv'] = get_without_pdw(self.price_contract_by_month)
        ###aditional services
        #######################
        data['stage_property_data'] = stage_property_data
        ##data['total_price_with_pdv'] = self.price_contract
        ##data['pdv'] = get_pdv(data['total_price_with_pdv'])
        data['total_price'] = get_without_pdw(self.price_contract)
        details_1 = ContractProducts.objects.filter(contract=self).values('product', 'product__name', 'count', 'price',
                                                                          'pdv', 'total_price', 'total_price_pdv')
        details_2 = ContractSubscription.objects.filter(contract=self).values('product', 'product__s_count',
                                                                              'product__name', 'count',
                                                                              'price', 'pdv', 'total_price',
                                                                              'total_price_pdv', 'start_period',
                                                                              'end_period')
        data['details'] = list(details_1) + list(details_2)
        data['add_user_cost'] = Subscription.objects.get(pk=6).as_dict(
            ['price', 'pdv', 'price_pdv'])  ##Доплата до тарифного плану за кожного додаткового користувача
        data['one_mb_cost'] = Product.objects.get(pk=17).as_dict(
            ['price', 'pdv', 'price_pdv'])  ##Вартість передачі 1-го МБ понад тариф

        ################products##################
        data['products'] = {}
        data['products']['details'] = list(details_1)
        data['products']['total_price'] = details_1.aggregate(Sum('total_price'))['total_price__sum'] or 0
        data['products']['pdv'] = details_1.aggregate(Sum('pdv'))['pdv__sum'] or 0
        data['products']['total_price_pdv'] = details_1.aggregate(Sum('total_price_pdv'))['total_price_pdv__sum'] or 0
        ##########################################
        data['subscription'] = {}
        data['subscription']['details'] = details_2
        data['mb_count'] = int(ContractSubscription.objects.filter(contract=self).values('product__s_count').aggregate(
            Sum('product__s_count'))['product__s_count__sum'] or 0)
        data['user_count'] = int(ContractSubscription.objects.filter(contract=self).values('count').aggregate(
            Sum('count'))['count__sum'] or 0)
        data['total_price_with_pdv_locale'] = num2words(data['total_price_with_pdv'] + .00, lang='uk', to='currency',
                                                        currency='UAH')
        data['connection_payment'] = self.get_connection_payment()

        return data

    def get_connection_payment(self):
        if self.statement.statement_type == 'integration':
            connection_payment = ContractProducts.objects.filter(product__pk=16, contract=self).values('product',
                                                                                                       'product__name',
                                                                                                       'count', 'price',
                                                                                                       'pdv',
                                                                                                       'total_price',
                                                                                                       'total_price_pdv')
        else:
            connection_payment = ContractProducts.objects.filter(product__pk=14, contract=self).values('product',
                                                                                                       'product__name',
                                                                                                       'count', 'price',
                                                                                                       'pdv',
                                                                                                       'total_price',
                                                                                                       'total_price_pdv')
        return list(connection_payment)[0]

    def get_template_name(self):
        if self.statement.statement_type == 'integration':
            if self.statement.contractor.bank == 'K':
                return 'contracts_integration_k'
            else:
                return 'contracts_integration_b'
        if self.statement.statement_type == 'web':
            if self.statement.contractor.bank == 'K':
                return 'contracts_web_k'
            else:
                return 'contracts_web_b'

    def generate_doc_and_save(self):
        return self.generate_doc(save_in_contract=True)

    def generate_doc(self, save_in_contract=True):
        data = self.get_doc_data()
        ##print(data)
        template_name = self.get_template_name()
        from dict_register.models import TemplateDocument
        template_obj = TemplateDocument.objects.get(related_model_name=template_name)
        docx_template = template_obj.template_file.path
        doc = docxtpl.DocxTemplate(docx_template)
        doc.render(data)

        upload_to = datetime.today().strftime('uploads/contract_docx/%Y/%m/%d/')
        base_dir = os.path.join(MEDIA_ROOT, upload_to)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        filename = get_random_string(length=32) + '.docx'
        out_path = os.path.join(base_dir, filename)
        doc.save(out_path)
        relative_file_name = os.path.join(upload_to, filename)

        if save_in_contract:
            self.contract_docx.name = relative_file_name
            self.save()

        return relative_file_name

    def get_pay_periods(self, end_date=None):
        period_list = []
        start_date = self.start_accrual

        if type(start_date) == datetime:
            first_date = start_date.date()
        else:
            first_date = start_date

        end_date = end_date or self.expiration_date
        ##raise Exception(start_date)

        print('start_date -> ', str(start_date))
        print('end_date -> ', str(end_date))
        month_range = ((end_date.year - start_date.year) * 12 - start_date.month) + end_date.month
        ##raise Exception(month_range)
        ##print('month_range -> ', str(month_range))
        for month_index in range(month_range + 1):
            year = first_date.year
            ##print('first_date -> ', str(first_date))
            ##print('month_index -> ',month_index)
            month = (start_date + relativedelta(months=+month_index)).month
            ##print('month -> ',month)
            last_day_of_month = calendar.monthrange(year, month)[1]

            last_date = date(year, month, last_day_of_month)
            ##print('last_date:',type(last_date),'first_date:',type(first_date))
            interval = (last_date - first_date).days
            period_list.append({"start_date": first_date, "end_date": last_date, "interval": interval})
            ##print('last_date -> ', str(last_date))
            first_date = last_date + relativedelta(days=+1)
        ##print('pay_periods -> ', str(period_list))
        return period_list

    def refresh_balance(self):
        self.save()


class ProductMixin(object):
    def calculate_price_if_not_set(self):
        if not self.price:
            self.price = self.product.price
            self.total_price = self.count * self.price
            self.pdv = get_pdv(self.total_price)
            self.total_price_pdv = self.total_price + self.pdv


class XXXProducts(ProductMixin, CoreBase):
    product = models.ForeignKey('dict_register.Product', on_delete=models.CASCADE)
    count = models.IntegerField(default=1)
    price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)
    pdv = models.FloatField(default=0)
    total_price_pdv = models.FloatField(default=0)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.calculate_price_if_not_set()
        super(XXXProducts, self).save(*args, **kwargs)


class XXXSubscription(ProductMixin, CoreBase):
    product = models.ForeignKey('dict_register.Subscription', on_delete=models.CASCADE)
    charging_day = models.IntegerField()
    start_period = models.DateField()
    end_period = models.DateField()
    count = models.IntegerField(default=1)
    price = models.FloatField(default=0)
    total_price = models.FloatField(default=0)
    pdv = models.FloatField(default=0)
    total_price_pdv = models.FloatField(default=0)

    class Meta:
        abstract = True

    def calculate_dates_if_not_set(self):
        if not self.start_period or not self.end_period:
            self.start_period = self.contract.start_accrual
            self.end_period = self.contract.expiration_date

    def save(self, *args, **kwargs):
        self.charging_day = 20
        self.calculate_price_if_not_set()

        self.calculate_dates_if_not_set()
        super(XXXSubscription, self).save(*args, **kwargs)


class ContractProducts(XXXProducts):
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = u'Послуги(товари) по договору'
        verbose_name = u'Послуги(товари) по договору'

    def __str__(self):
        return str(self.product)


class ContractSubscription(XXXSubscription):
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = u'Послуги(товари) по договору'
        verbose_name = u'Послуги(товари) по договору'

    def __str__(self):
        return str(self.product)


class AccrualProducts(XXXProducts):
    accrual = models.ForeignKey('RegisterAccrual', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = u'Послуги(товари) по договору'
        verbose_name = u'Послуги(товари) по договору'


class AccrualSubscription(XXXSubscription):
    accrual = models.ForeignKey('RegisterAccrual', on_delete=models.CASCADE)

    class Meta:
        verbose_name_plural = u'Послуги(товари) по договору'
        verbose_name = u'Послуги(товари) по договору'


class StageProperty(CoreBase):
    """"""
    contract = models.OneToOneField('Contract',
                                    on_delete=models.CASCADE, verbose_name="Договір")
    name = models.TextField(default='', verbose_name="Назва організації", null=True, blank=True)
    address = models.TextField(default='', null=True, blank=True)
    settlement_account = models.CharField(max_length=30, verbose_name="Розрахунковий рахунок", null=True, blank=True)
    bank_name = models.CharField(max_length=200, null=True, verbose_name="Назва банку")
    main_unit = models.CharField(max_length=200, blank=True, null=True, verbose_name="Уповноважена особа")
    main_unit_state = models.CharField(max_length=200, blank=True, null=True, verbose_name="Посада уповноваженої особи")
    mfo = models.CharField(max_length=50, null=True, blank=True, verbose_name='МФО')
    ipn = models.CharField(max_length=200, blank=True, null=True, verbose_name="ІПН")
    certificate_number = models.CharField(max_length=200, blank=True, null=True, verbose_name="Номер свідотства ПДВ")
    edrpou = models.CharField(max_length=10, verbose_name="ЄДРПОУ", null=True, blank=True)
    phone = models.CharField(max_length=150, verbose_name="Телефон", null=True, blank=True)
    email = models.CharField(max_length=150, verbose_name="email", null=True, blank=True)
    work_reason = models.TextField(null=True, verbose_name="Працює на підставі")
    statute_copy = models.FileField(null=True, verbose_name="Статутні документи")

    class Meta:
        verbose_name_plural = u'Реквізити договорів'
        verbose_name = u'Реквізити договору'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return 'Реквізити {0}'.format(str(self.contract) or '-')

    def load_from_statemant(self):
        statement = self.contract.statement
        contractor = statement.contractor
        self.name = contractor.full_name
        self.main_unit_state = contractor.main_unit_state
        self.main_unit = contractor.main_unit
        self.edrpou = contractor.edrpou
        self.bank_name = contractor.bank_name
        self.mfo = contractor.mfo
        self.ipn = contractor.ipn
        self.certificate_number = contractor.certificate_number
        self.address = contractor.address
        self.settlement_account = contractor.settlement_account
        self.phone = contractor.phone
        self.email = contractor.email
        self.work_reason = contractor.work_reason
        self.statute_copy = contractor.statute_copy


class Coordination(CoreBase):
    subject = models.TextField(verbose_name='Особа')
    status = models.BooleanField(default=False, verbose_name="Статус погодження (Так/Ні)")
    start = models.DateField(verbose_name="Початок погодження")
    end = models.DateField(verbose_name="Кінець погодження")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name_plural = u'Погодження договорів'
        verbose_name = u'Погодження договору'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0} {1}'.format(str(self.subject), str(self.status))


class ContractFinance(CoreBase):
    """Містить загальну інформацію про фінансову частину договорів"""
    contract = models.OneToOneField('Contract', editable=False,
                                    on_delete=models.CASCADE, verbose_name="Договір")
    last_date_accrual = models.DateField(null=True, verbose_name="Дата останніх нарахувань")
    total_size_accrual = models.FloatField(default=0, verbose_name="Розмір нарахувань (Загальний)")
    last_date_pay = models.DateField(null=True, verbose_name="Дата останніх нарахувань")
    total_size_pay = models.FloatField(default=0, verbose_name="Розмір нарахувань (Загальний)")
    total_balance = models.FloatField(default=0, verbose_name="Баланс")

    class Meta:
        verbose_name_plural = u'Баланс по договорах'
        verbose_name = u'Баланс по договору'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return 'Баланс по договору {0}'.format(self.contract or '-')

    def get_total_size_accrual(self):
        if self.contract:
            return self.contract.registeraccrual_set.all().aggregate(Sum('size_accrual'))['size_accrual__sum'] or 0

    def get_total_size_pay(self):
        if self.contract:
            return self.contract.registerpayment_set.all().aggregate(Sum('sum_payment'))['sum_payment__sum'] or 0

    def get_last_accrual_date(self):
        if self.contract:
            accruals = RegisterAccrual.objects.filter(contract=self.contract).order_by('-date_accrual')
            if accruals.count() > 0:
                return accruals[0].date_accrual

    def get_total_balance(self):
        if self.contract:
            return ((self.total_size_pay or 0.00) - (self.total_size_accrual or 0.00))

    def set_one_time_pay(self):
        try:
            accrual = RegisterAccrual.objects.get(contract=self.contract)
        except ObjectDoesNotExist:
            accrual = None
        if not accrual:
            accrual = RegisterAccrual(contract=self.contract, size_accrual=self.contract.price_contract,
                                      date_accrual=self.contract.start_date)
            accrual.save()

    def set_finance_values(self):
        if self.contract.one_time_service:
            self.set_one_time_pay()
        else:
            self.total_size_accrual = self.get_total_size_accrual()
            self.total_size_pay = self.get_total_size_pay()
            self.total_balance = self.get_total_balance()
            self.last_date_accrual = self.get_last_accrual_date()


class PayPlan(CoreBase):
    """ План платежів """
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, verbose_name="Договір")
    pay_order = models.PositiveIntegerField(verbose_name="Порядковий номер")
    date_start_period = models.DateField(null=True, verbose_name="Початок періоду")
    date_end_period = models.DateField(null=True, verbose_name="Кінець періоду")
    date_accrual = models.DateField(verbose_name="Дата нарахувань")
    date_pay = models.DateField(verbose_name="Дата кінцева дата оплати")
    size_accrual = models.FloatField(verbose_name="Плановий платіж")

    class Meta:
        verbose_name_plural = u'Плани платежів'
        verbose_name = u'План платежів'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return 'Плановий платіж у розмірі {0} грн до договору {1} за період {2} {3}'.format(self.size_accrual or '0',
                                                                                            self.contract.__str__(),
                                                                                            self.date_start_period,
                                                                                            self.date_end_period)

    def save(self, *args, **kwargs):
        self.set_pay_order()
        super(PayPlan, self).save(*args, **kwargs)

    def set_pay_order(self):
        if not self.pay_order:
            count = PayPlan.objects.filter(contract=self.contract).count()
            self.pay_order = count + 1

    @classmethod
    def calc_non_regular_accruals(cls, contract, order, period):
        size_accrual = contract.get_contract_product_price()
        date_pay = period.get('start_date') + relativedelta(days=+5)
        plan_accrual = cls(contract=contract, pay_order=order,
                           date_start_period=period.get('start_date'),
                           date_end_period=period.get('start_date'),
                           date_accrual=period.get('start_date'),
                           date_pay=date_pay,
                           size_accrual=size_accrual)
        plan_accrual.save()

    @classmethod
    def calc_accruals(cls, contract):
        pay_periods = contract.get_pay_periods()
        order = cls.objects.filter(contract=contract).count() + 1 or 1

        cls.calc_non_regular_accruals(contract, 0, pay_periods[0])

        for period in pay_periods:
            start_date = period.get('start_date')
            ##Перевіряємо тип організації, якщо комерційний банк то виставляємо рахунок наперед
            if contract.contractor.bank == 'K':
                date_accrual = period.get('start_date')
            else:
                date_accrual = period.get('end_date')

            size_accrual = contract.price_contract_by_month
            date_pay = date_accrual + relativedelta(days=+5)
            plan_accrual = cls(contract=contract, pay_order=order, date_start_period=start_date,
                               date_end_period=date_accrual,
                               date_accrual=date_accrual, date_pay=date_pay,
                               size_accrual=size_accrual)
            plan_accrual.save()
            order += 1


class RegisterAccrual(CoreBase):
    """ Реєстр нарахувань (Рахунків) """
    title = models.CharField(verbose_name='Заголовок рахунку', max_length=150, null=True)
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, verbose_name="Договір")
    date_start_period = models.DateField(null=True, verbose_name="Початок періоду")
    date_end_period = models.DateField(null=True, verbose_name="Кінець періоду")
    date_accrual = models.DateField(null=True, verbose_name="Дата нарахувань")
    mb_size = models.FloatField(null=True, verbose_name="Кількість мегабайт (фактично)")
    mb_size_tariff = models.FloatField(null=True, verbose_name="Кількість мегабайт в тарифі")
    mb_size_over_tariff = models.FloatField(null=True, verbose_name="Кількість мегабайт понад тариф")
    size_accrual = models.FloatField(null=True, verbose_name="Розмір нарахувань")
    pay_size = models.FloatField(null=True, verbose_name="Сума до сплати")
    balance = models.FloatField(null=True, verbose_name="Баланс")
    penalty = models.FloatField(null=True, verbose_name="Пеня за попередній період")
    accrual_docx = models.FileField(upload_to='uploads/accrual_docx/%Y/%m/%d/', null=True,
                                    verbose_name="Проект Рахунку")
    date_sending_doc = models.DateField(verbose_name="Дата відправлення акту", null=True)
    is_doc_send_successful = models.NullBooleanField(verbose_name="Акт успішно відправлено?", )

    @classmethod
    def calculate_penalty(cls, balance, delay):
        if balance > 0:
            return 0

        if delay < 1:
            return 0

        balance = balance * -1
        p1 = balance * 0.03
        p2 = (balance * 0.001) * delay
        p3 = balance * 0.07 if delay > 30 else 0
        return p1 + p2 + p3

    @classmethod
    def calculate_non_regular_accrual(cls, contract):
        logger.debug('RUN: calculate_non_regular_accrual')
        pay_periods = contract.get_pay_periods()
        period = pay_periods[0]
        start_date = period.get('start_date')

        total_price_pdv = contract.get_contract_product_price()
        if total_price_pdv > 0:
            if cls.objects.filter(contract=contract).count() > 0:
                return {'message': 'accrual alredy exist'}
            accrual = cls(contract=contract,
                          title='Послуги',
                          date_start_period=start_date,
                          date_end_period=start_date,
                          size_accrual=total_price_pdv,
                          date_accrual=start_date,
                          balance=-total_price_pdv,
                          pay_size=total_price_pdv,
                          penalty=0.00)
            accrual.save()
            ## Одноразові послуги чи товари
            contract_products = ContractProducts.objects.filter(contract=contract)
            for contract_product in contract_products:
                accrual_product = AccrualProducts(accrual=accrual, product=contract_product.product,
                                                  count=contract_product.count, price=contract_product.price,
                                                  total_price=contract_product.total_price, pdv=contract_product.pdv,
                                                  total_price_pdv=contract_product.total_price_pdv)
                accrual_product.save()
                logger.info(accrual_product)
            ## Одноразові послуги чи товари
            accrual.set_docx()
            accrual.save()
            ## Створення АКТУ ВИКОНАНИХ ПОСЛУГ
            number_act = u"Акт №{} до договору № {}".format(accrual.date_accrual.strftime("%m"),
                                                            accrual.contract.number_contract)
            act = RegisterAct(number_act=number_act, accrual=accrual, contract=accrual.contract,
                              date_formation_act=accrual.date_accrual)
            act.save()
            act.generate_act_docs()
            ## Створення АКТУ ВИКОНАНИХ ПОСЛУГ

    @classmethod
    def calculate_accruals(cls, contract: Contract = None, start_date=None, end_date=None, create_pdf=None) -> List:
        cls.calculate_non_regular_accrual(contract)
        res = []  ##return  result
        now = datetime.today()
        ##month = now.month - 1 or 12
        ##year = now.year if now.month - 1 > 0 else now.year - 1
        ##last_day_of_month = calendar.monthrange(year, month)[1]
        month = now.month
        year = now.year
        last_day_of_month = calendar.monthrange(year, month)[1]
        _end_date = date(year, month, last_day_of_month)
        end_date = end_date or _end_date

        pay_periods = contract.get_pay_periods(end_date=end_date)
        ##raise Exception(pay_periods)

        logger.debug(f'Pay_periods: {pay_periods}')
        n = 0
        for period in pay_periods:
            ## <-- Порівнюємо платежі за попередній період з нарахуваннями
            last_period_q = cls.objects.filter(date_start_period__lte=period.get('start_date'),
                                               contract=contract).order_by('-date_start_period')

            balance_by_last_period = (last_period_q.aggregate(Sum('size_accrual'))['size_accrual__sum'] or 0) * -1 or 0
            if last_period_q.count():
                logger.debug(f' Last period date: {last_period_q[0].date_start_period}')
                logger.debug(f' Last period balanse: {last_period_q[0].balance}')

            payments = RegisterPayment.objects.filter(contract=contract, payment_date__lte=period.get('end_date'),
                                                      payment_date__gte=period.get('start_date')).aggregate(
                Sum('sum_payment'))['sum_payment__sum'] or 0
            ## Порівнюємо платежі за попередній період з нарахуваннями -->
            balance = balance_by_last_period + payments - contract.price_contract_by_month
            logger.debug(f'Balance: {balance}')
            logger.debug(f'Iteration: {n}')
            q = cls.objects.filter(date_start_period=period.get('start_date'), date_end_period=period.get('end_date'),
                                   contract=contract)
            logger.debug(f'Period exist?: {q.count()}')
            if q.count() > 0:
                continue

            pay_size = balance * -1 if balance < 0 else 0
            logger.debug(f'Pay size: {pay_size}')
            ###

            accrual = cls(contract=contract,
                          title='Абонплата',
                          date_start_period=period.get('start_date'),
                          date_end_period=period.get('end_date'),
                          size_accrual=contract.price_contract_by_month,
                          date_accrual=period.get('start_date'),
                          balance=balance,
                          pay_size=pay_size,
                          penalty=0)
            accrual.save()

            contract_subscriptions = ContractSubscription.objects.filter(contract=contract)
            for contract_subscription in contract_subscriptions:
                AccrualSubscription.objects.create(accrual=accrual,
                                                   charging_day=contract_subscription.charging_day,
                                                   start_period=period.get('start_date'),
                                                   end_period=period.get('end_date'),
                                                   product=contract_subscription.product,
                                                   count=contract_subscription.count,
                                                   price=contract_subscription.price,
                                                   total_price=contract_subscription.total_price,
                                                   pdv=contract_subscription.pdv,
                                                   total_price_pdv=contract_subscription.total_price_pdv)
            accrual.set_docx()
            accrual.save()
            ## Створення АКТУ ВИКОНАНИХ ПОСЛУГ
            number_act = u"Акт №{} до договору № {}".format(accrual.date_accrual.strftime("%m"),
                                                            accrual.contract.number_contract)
            act = RegisterAct(number_act=number_act, accrual=accrual, contract=accrual.contract,
                              date_formation_act=accrual.date_accrual)
            act.save()
            act.generate_act_docs()
            ## Створення АКТУ ВИКОНАНИХ ПОСЛУГ
            res.append({'period': period, 'status': 'success', 'size_accrual': contract.price_contract_by_month})
            n += 1
        return res

    def generate_docx_invoice(self, doc=None):
        """ Return *.docx path from MEDIA_ROOT """
        logger.debug(' start function "generate_docx_invoice"')
        if not doc:
            from dict_register.models import TemplateDocument
            template_obj = TemplateDocument.objects.get(related_model_name='registerinvoice')
            docx_template = template_obj.template_file.path
            doc = docxtpl.DocxTemplate(docx_template)

        upload_to = datetime.today().strftime('uploads/accrual_docx/%Y/%m/%d/')
        base_dir = os.path.join(MEDIA_ROOT, upload_to)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        filename = get_random_string(length=32) + '.docx'
        out_path = os.path.join(base_dir, filename)

        ret = os.path.join(upload_to, filename)

        data = self.get_invoice_data()
        logger.debug(' end function "generate_docx_invoice"')
        doc.render(data)
        doc.save(out_path)
        return ret

    def get_reg_number(self):
        return f'РФ-{self.id}'

    def get_invoice_data(self):
        logger.debug('start function "get_invoice_data"')
        data = {}
        contract = self.contract
        data['number_contract'] = str(contract.number_contract)
        data['reg_number'] = self.get_reg_number()
        local_contract_date = format_datetime(contract.start_date, "«d» MMMM Y", locale='uk_UA')
        data['local_contract_date'] = local_contract_date
        data['subject_contract'] = contract.subject_contract
        data['price_contract_by_month'] = float(self.size_accrual or 0.00)
        price_contract_by_month_locale = num2words(self.size_accrual + 0.00, lang='uk', to='currency',
                                                   currency='UAH')
        data['price_contract_by_month_locale'] = price_contract_by_month_locale
        data['total_price'] = self.pay_size
        data['pdv'] = get_pdv(self.pay_size)
        data['total_price_no_pdv'] = round(self.pay_size - data['pdv'], 2)
        data['debt'] = round(self.balance + self.size_accrual, 2)
        data['price_locale'] = num2words(data['total_price'] + 0.00, lang='uk', to='currency',
                                         currency='UAH')
        data['act_date_locale'] = format_datetime(self.date_accrual, "«d» MMMM Y", locale='uk_UA')
        local_month_name = LOCAL_MONTH[self.date_accrual.month]
        data['spatial_date'] = '{} {}'.format(local_month_name, self.date_accrual.year)
        stage_property_q = StageProperty.objects.filter(contract=contract)
        if stage_property_q.count() > 0:
            stage_property = stage_property_q[0]
            stage_property_data = {'name': stage_property.name,
                                   'address': stage_property.address,
                                   'bank_name': stage_property.bank_name,
                                   'settlement_account': stage_property.settlement_account,
                                   'certificate_number': stage_property.certificate_number,
                                   'mfo': stage_property.mfo,
                                   'edrpou': stage_property.edrpou,
                                   'phone': stage_property.phone
                                   }
        else:
            stage_property_data = None

        data['stage_property_data'] = stage_property_data
        details_1 = AccrualProducts.objects.filter(accrual=self).values('product', 'product__name', 'count', 'price',
                                                                        'pdv', 'total_price', 'total_price_pdv')
        details_2 = AccrualSubscription.objects.filter(accrual=self).values('product', 'product__name', 'count',
                                                                            'price', 'pdv', 'total_price',
                                                                            'total_price_pdv', 'start_period',
                                                                            'end_period')
        data['details'] = list(details_1) + list(details_2)
        logger.debug(' end function "get_invoice_data"')
        return data

    class Meta:
        verbose_name_plural = u'Нарахування'
        verbose_name = u'Нарахування'

    def set_docx(self):
        self.accrual_docx = self.generate_docx_invoice()

    def save(self, *args, **kwargs):

        super(RegisterAccrual, self).save()

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return 'Нарахування у розмірі {0} до договору {1}'.format(self.size_accrual or '0', self.contract.__str__())


class RegisterPayment(CoreBase):
    PAYMENT_CHOICES = [['import', 'Клієнт-банк'],
                       ['handly', 'Вручну'], ]
    contract = models.ForeignKey('Contract',
                                 on_delete=models.CASCADE, verbose_name="Договір")
    payment_date = models.DateField(null=True, verbose_name="Дата оплати")
    outer_doc_number = models.CharField(max_length=100, null=True,
                                        verbose_name='Зовнішній номер документа платежу')
    act = models.ForeignKey('RegisterAct', related_name='payments',
                            null=True, blank=True, editable=False,
                            on_delete=models.CASCADE, verbose_name="Акт")
    payment_type = models.CharField(default=PAYMENT_CHOICES[1][0], max_length=100, choices=PAYMENT_CHOICES)
    sum_payment = models.IntegerField(null=True, verbose_name="Число")
    importer = models.ForeignKey('contracts.ImportPayment', on_delete=models.CASCADE, null=True,
                                 verbose_name='Назва завантаження')

    class Meta:
        verbose_name_plural = u'Платежі'
        verbose_name = u'Платіж'

    def __str__(self):
        return self.__unicode__()

    def get_pay_date(self):
        if self.payment_date:
            return self.payment_date.strftime("%m/%d/%Y")
        else:
            return '<не вказано>'

    def __unicode__(self):
        return u'платіж у розмірі {0} від {1} "{2}"'.format(self.sum_payment or '0', self.get_pay_date(),
                                                            self.contract.contractor)


class RegisterAct(CoreBase):
    number_act = models.TextField(verbose_name="Номер акту")
    contract = models.ForeignKey('Contract', on_delete=models.CASCADE, verbose_name="Договір")
    accrual = models.ForeignKey('RegisterAccrual', null=True, blank=True, editable=False,
                                on_delete=models.CASCADE, verbose_name="Нарахування")
    date_formation_act = models.DateField(verbose_name="Дата формування акту")
    date_sending_act = models.DateField(verbose_name="Дата відправлення акту", null=True)
    is_send_successful = models.NullBooleanField(verbose_name="Акт успішно відправлено?", )
    date_return_act = models.DateField(verbose_name="Дата повернення акту", null=True, )
    copy_act = models.FileField(null=True, upload_to='uploads/docx_act/%Y/%m/%d/', verbose_name="Копія акту(DOCX)")
    copy_act_pdf = models.FileField(null=True, upload_to='uploads/pdf_act/%Y/%m/%d/', verbose_name="Копія акту(PDF)")

    class Meta:
        verbose_name_plural = u'Акти'
        verbose_name = u'Акт'

    def save(self, *args, **kwargs):
        super(RegisterAct, self).save(*args, **kwargs)

    @classmethod
    def generate_acts(cls, regenerate_all=None):
        from dict_register.models import TemplateDocument
        template_obj = TemplateDocument.objects.get(related_model_name='registeract')
        docx_template = template_obj.template_file.path
        doc = docxtpl.DocxTemplate(docx_template)
        res = []
        if regenerate_all:
            acts = cls.objects.all()
        else:
            acts = cls.objects.filter(copy_act__exact=None)
        for act in acts:
            act_docx_file = act.generate_docx_act(doc=doc)
            act.copy_act.name = act_docx_file
            act_pdf_file = act.convert_docx_to_pdf()
            act.copy_act_pdf.name = act_pdf_file
            act.save()
            res.append(str(act))

        return res

    def generate_act_docs(self):
        act_docx_file = self.generate_docx_act()
        self.copy_act.name = act_docx_file
        ##act_pdf_file = self.convert_docx_to_pdf()
        ##self.copy_act_pdf.name = act_pdf_file
        self.save()
        return {'copy_act': self.copy_act.name}  # , 'copy_act_pdf': self.copy_act_pdf.name}

    def generate_docx_act(self, doc=None):
        """ Return *.docx path from MEDIA_ROOT """
        logger.debug(' start function "generate_docx_act"')
        if not doc:
            from dict_register.models import TemplateDocument
            template_obj = TemplateDocument.objects.get(related_model_name='registeract')
            docx_template = template_obj.template_file.path
            doc = docxtpl.DocxTemplate(docx_template)

        upload_to = datetime.today().strftime('uploads/docx_act/%Y/%m/%d/')
        base_dir = os.path.join(MEDIA_ROOT, upload_to)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        filename = get_random_string(length=32) + '.docx'
        out_path = os.path.join(base_dir, filename)

        ret = os.path.join(upload_to, filename)

        data = self.get_act_data()
        logger.debug(' end function "generate_docx_act"')
        doc.render(data)
        doc.save(out_path)
        return ret

    def get_act_data(self):
        logger.debug('start function "get_act_data"')
        data = {}
        contract = self.contract
        data['number_contract'] = str(contract.number_contract)
        local_contract_date = format_datetime(contract.start_date, "«d» MMMM Y", locale='uk_UA')
        data['local_contract_date'] = local_contract_date
        data['subject_contract'] = contract.subject_contract
        data['price_contract_by_month'] = float(self.accrual.size_accrual or 0.00)
        price_contract_by_month_locale = num2words(self.accrual.size_accrual + 0.00, lang='uk', to='currency',
                                                   currency='UAH')
        data['price_contract_by_month_locale'] = price_contract_by_month_locale

        pdv = round(self.accrual.size_accrual / 120 * 20, 2)  ## розмір пдв
        data['pdv'] = pdv
        pdv_locale = num2words(pdv + 0.00, lang='uk', to='currency',
                               currency='UAH')
        data['pdv_locale'] = pdv_locale
        data['price'] = round(self.accrual.size_accrual - pdv, 2)
        data['price_locale'] = num2words(data['price'] + 0.00, lang='uk', to='currency',
                                         currency='UAH')

        data['act_date_locale'] = format_datetime(self.date_formation_act, "«d» MMMM Y", locale='uk_UA')

        local_month_name = LOCAL_MONTH[self.date_formation_act.month]

        data['spatial_date'] = '{} {}'.format(local_month_name, self.date_formation_act.year)

        stage_property_q = StageProperty.objects.filter(contract=contract)
        if stage_property_q.count() > 0:
            stage_property = stage_property_q[0]
            stage_property_data = {'name': stage_property.name,
                                   'address': stage_property.address,
                                   'bank_name': stage_property.bank_name,
                                   'settlement_account': stage_property.settlement_account,
                                   'certificate_number': stage_property.certificate_number,
                                   'mfo': stage_property.mfo,
                                   'edrpou': stage_property.edrpou,
                                   'phone': stage_property.phone
                                   }

        else:
            stage_property_data = None

        data['stage_property_data'] = stage_property_data
        details_1 = AccrualProducts.objects.filter(accrual=self.accrual).values('product', 'product__name', 'count',
                                                                                'price', 'pdv', 'total_price',
                                                                                'total_price_pdv')
        details_2 = AccrualSubscription.objects.filter(accrual=self.accrual).values('product', 'product__name', 'count',
                                                                                    'price', 'pdv', 'total_price',
                                                                                    'total_price_pdv', 'start_period',
                                                                                    'end_period')
        data['details'] = list(details_1) + list(details_2)
        logger.debug(' end function "get_act_data"')
        return data

    def convert_docx_to_pdf(self):
        """ Return *.pdf path from MEDIA_ROOT """
        upload_to = datetime.today().strftime('uploads/pdf_act/%Y/%m/%d/')
        source = self.copy_act.path
        out_path = os.path.join(MEDIA_ROOT, upload_to)
        filename = os.path.basename(source).replace('.docx', '.pdf')
        ret = os.path.join(upload_to, filename)
        out_file = os.path.join(out_path, filename)
        LibreOfficeConverter.convert_to_pdf(source, out_file)
        return ret

    def send_act(self):
        ##TODO
        ##1. Отримати пошту контрагента
        ##2. Сформувати акт (generate_act)
        ##3. Перегнати акт з docx в pdf
        ##3. Відправити акт по пошті
        ##4. Якщо відправлено успішно змінюємо статус акту
        pass

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return u'{}'.format(self.number_act or '-')


class RegisterTemplateDocument(CoreBase):
    name = models.TextField(verbose_name="Назва")
    sending_template = models.TextField(null=True, verbose_name="Посилання на шаблон")
    group_template = models.ForeignKey('dict_register.TemplateDocument', null=True, blank=True, editable=False,
                                       on_delete=models.PROTECT, verbose_name="Група шаблонів")

    class Meta:
        verbose_name_plural = u'Шаблон документів'
        verbose_name = u'Шаблон документа'
