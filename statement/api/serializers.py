from __future__ import unicode_literals
##from typing import Dict, List, AnyStr
##import json
from abc import ABCMeta, abstractmethod

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.serializers import ValidationError
from drf_yasg.utils import swagger_auto_schema
from django.http.request import HttpRequest
from drf_yasg import openapi
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from django.apps import apps
from l_core.cryptoserver.api import CryptoClient
from rest_framework.exceptions import APIException
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from sync_client.authentication import SyncClientAuthentication
from rest_framework.authentication import TokenAuthentication
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from l_core.models import CoreOrganization
from l_core.api.base.serializers import DynamicFieldsModelSerializer, BaseViewSetMixing

from statement.models import SEDStatement, AdditionalService
from l_core.api.base.serializers import CoreOrganizationSerializer
from l_core.fields import Base64FileField as AbstractBase64FileField
from dict_register.models import Subscription, Product
from rest_framework import viewsets


##SEDStatement-------------------------------------------------------
class SEDStatementSerializer(DynamicFieldsModelSerializer):
    contractor_expand = serializers.PrimaryKeyRelatedField(read_only=True)
    additional_services = serializers.SerializerMethodField()

    class Meta:
        model = SEDStatement
        fields = (
            "id", "reg_number", "ecp_certificate", "statement_date", "control_date", "statement_type", "__str__",
            "status", "contractor", "contractor_expand", "note", "int_integration_type", "int_access_to_SEV_OVV",
            "crypto_autograph_count", "statute_copy", "web_access_count",
            "statement_doc", "additional_services", "sign_is_valid",
            "web_tariff_plan", "is_send_to_technician", "is_contractor_connected")

    expandable_fields = {
        'contractor_expand': (
            CoreOrganizationSerializer, {'source': 'contractor', 'fields': ['id', '__str__']})
    }

    def get_additional_services(self, obj):
        data = []
        for service in AdditionalService.objects.filter(statement=obj):
            data.append({"product": service.product.name, "count": service.count})
        return data

    def __init__(self, *args, **kwargs):
        ##print('INIT: SEDStatementSerializer')
        super(SEDStatementSerializer, self).__init__(*args, **kwargs)


class SEDStatementSerializerPrivate(SEDStatementSerializer):
    def __init__(self, *args, **kwargs):
        ##print('INIT: SEDStatementSerializerPrivate')
        super(SEDStatementSerializerPrivate, self).__init__(*args, **kwargs)


class ServiceIntegration(serializers.Serializer):
    service = serializers.ChoiceField(required=True, choices=SEDStatement.STATEMENT_TYPE)
    integration_type = serializers.PrimaryKeyRelatedField(
        queryset=Subscription.objects.filter(service_type='integration'),
        required=True)
    number = serializers.CharField(max_length=150, required=True)
    auto_number = serializers.BooleanField(required=True)
    access_to_SEV_OVV = serializers.BooleanField(required=True)


class Company(serializers.Serializer):
    edrpou = serializers.CharField(required=False, max_length=8, min_length=8)
    certificate_number = serializers.CharField(required=False, max_length=30)
    full_name = serializers.CharField(required=True, max_length=256, min_length=3)
    name = serializers.CharField(required=False, max_length=256, min_length=3)

    def validate_company(self, data):
        validated_data = super(Company, self).validate(data)
        if not validated_data.get('edrpou'):
            raise ValidationError('Обовязково заповнити "edrpou"')


class RequiredIndividual(serializers.Serializer):
    ipn = serializers.CharField(required=True, max_length=30, label="Індивідуальний податковий номер")
    fiz_first_name = serializers.CharField(required=True, label="Імя")
    fiz_last_name = serializers.CharField(required=True, label="Прізвище")
    fiz_middle_name = serializers.CharField(required=True, label="По-батькові")
    passport = serializers.CharField(required=True, max_length=150, label="Серія та номер паспорта, або ІД картки")
    issuer = serializers.CharField(required=True, max_length=150, label="Ким виданий документ")
    issue_date = serializers.DateField(required=True, label="Коли виданий документ")


class Individual(serializers.Serializer):
    ipn = serializers.CharField(required=False, max_length=30, label="Індивідуальний податковий номер")
    fiz_first_name = serializers.CharField(required=False, label="Імя")
    fiz_last_name = serializers.CharField(required=False, label="Прізвище")
    fiz_middle_name = serializers.CharField(required=False, label="По-батькові")
    passport = serializers.CharField(required=False, label="Серія та номер паспорта, або ІД картки")
    issuer = serializers.CharField(required=False, label="Ким виданий документ")
    issue_date = serializers.CharField(required=False, label="Коли виданий документ")

    def validate_individual(self, data):
        validated_data = super(Individual, self).validate(data)
        required_serializer = RequiredIndividual(data=data)
        required_serializer.is_valid(raise_exception=True)


class Applicant(Individual, Company):
    def validate(self, data):
        validated_data = super(Applicant, self).validate(data)
        if not validated_data.get('edrpou') and not validated_data.get('ipn'):
            raise ValidationError('Обовязково заповнити "edrpou", або "ipn"')

        if validated_data.get('edrpou'):
            self.validate_company(data)

        if validated_data.get('ipn'):
            self.validate_individual(data)

        return validated_data


class CompanyNonRequired(Individual, Company):
    def validate(self, data):
        validated_data = super(CompanyNonRequired, self).validate(data)
        if not validated_data.get('edrpou') and not validated_data.get('ipn'):
            raise ValidationError('Обовязково заповнити "edrpou", або "ipn"')

        if validated_data.get('edrpou'):
            self.validate_company(data)

        return validated_data


class UserContacts(serializers.Serializer):
    first_name = serializers.CharField(required=True, max_length=256, min_length=3)
    last_name = serializers.CharField(required=True, max_length=256, min_length=3)
    middle_name = serializers.CharField(required=True, max_length=256, min_length=3)
    email = serializers.EmailField()
    phone = serializers.CharField(min_length=8, max_length=18, )


class Developer(serializers.Serializer):
    company_info = CompanyNonRequired()
    responsible_user = UserContacts()


class IntegrationSystem(serializers.Serializer):
    full_name = serializers.CharField(required=True, max_length=256, min_length=3)
    has_npa = serializers.BooleanField(required=True)
    developer = Developer()
    # ViewSets define the view behavior.


class Integrator(serializers.Serializer):
    company_info = CompanyNonRequired()
    responsible_user = UserContacts()


class Base64FileField(AbstractBase64FileField):
    class Meta:
        swagger_schema_fields = {
            "type": openapi.TYPE_STRING,
            "format": openapi.FORMAT_BASE64
        }


class Subject(Applicant):
    settlement_account = serializers.CharField(min_length=10, max_length=30)
    bank_name = serializers.CharField(max_length=256)
    mfo = serializers.CharField(max_length=10)
    main_unit = serializers.CharField(max_length=256)
    main_unit_state = serializers.CharField(max_length=256)
    taxation_method = serializers.CharField(max_length=256)
    main_unit_genitive = serializers.CharField(max_length=256)
    address = serializers.CharField(max_length=256)
    phone = serializers.CharField(max_length=256)
    email = serializers.EmailField()
    ##statute_copy = Base64FileField()


class IntegrationStatementSerializer(serializers.Serializer):
    service = ServiceIntegration()
    integrator = Integrator()
    integration_system = IntegrationSystem()
    subject = Subject()


####################################################

class ServiceWeb(serializers.Serializer):
    service = serializers.ChoiceField(required=True, choices=SEDStatement.STATEMENT_TYPE)
    web_access_type = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.filter(service_type='web'),
                                                         required=True)
    number = serializers.CharField(max_length=150, required=True)
    auto_number = serializers.BooleanField(required=True)


class WebStatementUserSerializer(UserContacts):
    phone = serializers.CharField(min_length=8, max_length=18, required=False)
    ACCESS_MODE_CHOICES = ["Працівник", "Виконавець"]
    access_mode = serializers.ChoiceField(choices=ACCESS_MODE_CHOICES, label="Режим доступу", required=True)
    state = serializers.CharField(max_length=256, label="Посада", required=True)


class WebAdditionalService(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all(),
                                                 required=True, label="Послуга")
    count = serializers.IntegerField(required=True, label="Кількість")


class WebStatementSerializer(serializers.Serializer):
    service = ServiceWeb()
    subject = Subject()
    users = serializers.ListField(child=WebStatementUserSerializer())
    additional_services = serializers.ListField(child=WebAdditionalService())



class VerifySing(serializers.Serializer):
    sign = serializers.CharField(required=True)
    unique_uuid = serializers.UUIDField(required=True)


class StatementInfo(serializers.Serializer):
    unique_uuid = serializers.UUIDField(required=True)




