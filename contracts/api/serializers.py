from __future__ import unicode_literals

from rest_framework import serializers
from l_core.api.base.serializers import DynamicFieldsModelSerializer

from contracts.models import Contract, RegisterAccrual, ContractFinance, RegisterPayment, RegisterAct, \
    RegisterTemplateDocument, StageProperty, Coordination, PayPlan, ContractSubscription, ContractProducts

from l_core.api.base.serializers import  CoreOrganizationSerializer

from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL


##Contract-------------------------------------------------------
class ContractFinanceSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ContractFinance
        fields = ('id', 'total_size_accrual', 'total_size_pay', 'total_balance')


##Contract-------------------------------------------------------
class ContractSerializer(DynamicFieldsModelSerializer):
    contractor_name = serializers.SerializerMethodField(read_only=True)
    contractfinance = ContractFinanceSerializer(read_only=True)
    contractor_data = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Contract
        fields = (
            'id', '__str__', 'statement', 'number_contract', 'parent_element', 'start_date', 'start_of_contract',
            'start_payment', 'status', "automatic_number_gen",
            'subject_contract', 'copy_contract', 'contractor', 'contractor_name', 'price_contract', 'contract_time',
            'expiration_date', 'price_contract_by_month', 'contractfinance', 'contract_docx', 'unique_uuid',
            'contractor_data')
        expandable_fields = {
            'contractor_data': (
                CoreOrganizationSerializer, {'source': 'contractor', })
        }

    def get_contractor_name(self, obj):
        if obj.contractor:
            return obj.contractor.__str__()


##RegisterAccrual-------------------------------------------------------
class RegisterAccrualSerializer(DynamicFieldsModelSerializer):
    contract = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RegisterAccrual
        fields = (
            'id', '__str__', 'date_accrual', 'size_accrual', 'balance', 'penalty', 'pay_size', 'contract', 'title',
            'accrual_docx', 'date_sending_doc', 'is_doc_send_successful')
        expandable_fields = {
            'contract': (
                ContractSerializer, {'source': 'contract', 'fields': ['id', '__str__']})
        }


##RegisterPayment-------------------------------------------------------
class RegisterPaymentSerializer(DynamicFieldsModelSerializer):
    contract_data = serializers.PrimaryKeyRelatedField(read_only=True)
    contractor_name = serializers.SerializerMethodField()

    class Meta:
        model = RegisterPayment
        fields = (
            'payment_date', 'id', 'sum_payment', 'payment_type', 'contract', '__str__', 'contract_data',
            'contractor_name',
            'outer_doc_number')
        expandable_fields = {
            'contract_data': (
                ContractSerializer, {'source': 'contract', 'fields': ['id', '__str__']})
        }

    def get_contractor_name(self, obj):
        if obj.contract:
            return obj.contract.contractor.__str__()


##RegisterAct-------------------------------------------------------
class RegisterActSerializer(DynamicFieldsModelSerializer):
    payments = RegisterPaymentSerializer(read_only=True, many=True)
    accrual = serializers.PrimaryKeyRelatedField(read_only=True)
    contract = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = RegisterAct
        fields = (
            'id', 'number_act', '__str__', 'date_formation_act', 'is_send_successful', 'date_sending_act',
            'date_return_act', 'accrual',
            'payments', 'copy_act', 'copy_act_pdf', 'contract')
        expandable_fields = {
            'accrual': (
                RegisterAccrualSerializer, {'source': 'accrual', 'fields': ['id', 'date_accrual', 'size_accrual']}),
            'contract': (
                ContractSerializer, {'source': 'contract', 'fields': ['id', '__str__', 'contractor']}),

        }


##RegisterTemplateDocument-------------------------------------------------------
class RegisterTemplateDocumentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = RegisterTemplateDocument
        fields = ("__all__")


##StageProperty-------------------------------------------------------
class StagePropertySerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StageProperty
        fields = (
            'id', '__str__', 'contract', 'name', 'address', 'settlement_account', 'mfo', 'edrpou', 'phone', 'bank_name',
            'ipn', 'main_unit', 'main_unit_state', 'certificate_number', 'email', 'statute_copy', 'work_reason')


##StageProperty-------------------------------------------------------
class PayPlanSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = PayPlan
        fields = (
            'id', '__str__', 'contract', 'date_accrual', 'date_pay', 'size_accrual', 'date_start_period',
            'date_end_period')


##ContractSubscription-------------------------------------------------------
class ContractSubscriptionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ContractSubscription
        fields = ('id', '__str__', 'count', 'price', 'pdv', 'total_price', 'total_price_pdv', 'product', 'contract')


##ContractProducts-------------------------------------------------------
class ContractProductsSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = ContractProducts
        fields = ('id', '__str__', 'count', 'price', 'pdv', 'total_price', 'total_price_pdv', 'product', 'contract')


##Coordination-------------------------------------------------------
class CoordinationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Coordination
        fields = ('id', '__str__', 'object_id', 'content_type', 'subject', 'status', 'start', 'end')


class calculateAccrualSerializer(serializers.Serializer):
    create_pdf = serializers.BooleanField()
    is_budget = serializers.BooleanField()
    is_comercial = serializers.BooleanField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class UploadCilentBanklSerializer(DynamicFieldsModelSerializer):
    class Meta:
        from contracts.models import ImportPayment
        model = ImportPayment
        fields = (
            'id', '__str__', 'in_file', 'details', 'is_imported', 'date_add')
