from rest_framework.decorators import api_view
from rest_framework.authentication import TokenAuthentication
from django.http import JsonResponse
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from l_core.api.base.serializers import BaseViewSetMixing
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.filters import SearchFilter, OrderingFilter
from sync_client.authentication import SyncClientAuthentication

from l_core.models import CoreOrganization
from statement.models import SEDStatement, AdditionalService
from .serializers import SEDStatementSerializer, SEDStatementSerializerPrivate, IntegrationStatementSerializer, \
    WebStatementSerializer, StatementInfo, VerifySing

from contracts.api.serializers import ContractSerializer


class SEDStatemantViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    permit_list_expands = ['contractor_expand']
    queryset = SEDStatement.objects.filter(verified=True, sign_is_valid=True)
    serializer_class = SEDStatementSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('reg_number',)
    filterset_fields = {
        'reg_number': ['icontains'],
        'statement_type': ['exact'],
        'contractor': ['exact'],
        'status': ['exact'],
        "is_send_to_technician": ['exact'],
        "is_contractor_connected": ['exact'],
    }

    def get_queryset(self):
        return self.queryset.filter(author=self.request.user)


class SEDStatemantPrivateViewSet(BaseViewSetMixing):
    authentication_classes = [SyncClientAuthentication]
    permission_classes = [IsAuthenticated]
    permit_list_expands = ['contractor_expand']
    queryset = SEDStatement.objects.filter(verified=True, sign_is_valid=True)
    serializer_class = SEDStatementSerializerPrivate
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('reg_number',)
    filterset_fields = {
        'reg_number': ['icontains'],
        'statement_type': ['exact'],
        'contractor': ['exact'],
        'status': ['exact'],
        "is_send_to_technician": ['exact'],
        "is_contractor_connected": ['exact'],
    }


@swagger_auto_schema(methods=['post'], request_body=IntegrationStatementSerializer)
@api_view(['POST'], )
def create_pdf_integration_statement(request):
    serializer = IntegrationStatementSerializer(data=request.data)
    if serializer.is_valid():
        contractor_data = serializer.validated_data.get('subject').copy()
        del contractor_data['main_unit_genitive']
        if request.user:
            contractor_data['author'] = request.user
        # try:
        #     contractor = CoreOrganization.objects.get(edrpou=contractor_data.get('edrpou'))
        # except CoreOrganization.DoesNotExist:
        contractor = CoreOrganization.objects.create(**contractor_data)

        integration_statement_data = dict(
            reg_number=serializer.validated_data.get('service').get('number'),
            statement_type=serializer.validated_data.get('service').get('service'),
            int_integration_type=serializer.validated_data.get('service').get('integration_type'),
            int_access_to_SEV_OVV=serializer.validated_data.get('service').get('access_to_SEV_OVV'),
            contractor=contractor,
            statute_copy=serializer.validated_data.get('statute_copy'),
            all_data=request.data)
        if request.user:
            integration_statement_data['author'] = request.user
        integration_statement, created = SEDStatement.objects.get_or_create(**integration_statement_data)

        _data = request.data.copy()
        _data['edrpou'] = contractor.edrpou or contractor.ipn

        SEDStatement.create_pdf_statement(_data, integration_statement)

        if not created:
            return Response({'non_field_errors': "Така заявка вже існує"}, status=status.HTTP_409_CONFLICT)
        return Response({'unique_uuid': integration_statement.unique_uuid,
                         'doc': integration_statement.get_doc_b64(),
                         'doc_url': request.build_absolute_uri(integration_statement.statement_doc.url),
                         })
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(methods=['post'], request_body=WebStatementSerializer)
@api_view(['POST'], )
def create_pdf_web_statement(request):
    serializer = WebStatementSerializer(data=request.data)
    if serializer.is_valid():
        contractor_data = serializer.validated_data.get('subject').copy()
        del contractor_data['main_unit_genitive']
        if request.user:
            contractor_data['author'] = request.user
        # try:
        #     contractor = CoreOrganization.objects.get(edrpou=contractor_data.get('edrpou'))
        # except CoreOrganization.DoesNotExist:
        contractor = CoreOrganization.objects.create(**contractor_data)

        web_statement_data = dict(
            reg_number=serializer.validated_data.get('service').get('number'),
            statement_type=serializer.validated_data.get('service').get('service'),
            web_tariff_plan=serializer.validated_data.get('service').get('web_access_type'),
            web_access_count=len(serializer.validated_data.get('users')),
            contractor=contractor,
            statute_copy=serializer.validated_data.get('statute_copy'),
            all_data=request.data)

        if request.user:
            web_statement_data['author'] = request.user

        web_statement, created = SEDStatement.objects.get_or_create(**web_statement_data)
        _data = request.data.copy()
        _data['edrpou'] = contractor.edrpou or contractor.ipn

        if not created:
            return Response({'non_field_errors': "Така заявка вже існує"}, status=status.HTTP_409_CONFLICT)

        ##calc additional services
        additional_services = serializer.validated_data.get('additional_services').copy()
        for service in additional_services:
            new_service = dict(product=service.get('product'),
                               count=service.get('count'),
                               statement=web_statement)
            AdditionalService.objects.create(**new_service)

        SEDStatement.create_pdf_statement(_data, web_statement)

        return Response({'unique_uuid': web_statement.unique_uuid,
                         'doc': web_statement.get_doc_b64(),
                         'doc_url': request.build_absolute_uri(web_statement.statement_doc.url),
                         })
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# @swagger_auto_schema(methods=['post'], request_body=VerifySing)
# @api_view(['POST'], )
# def verify_sign_by_crypto_server(request):
#     serializer = VerifySing(data=request.data)
#     if serializer.is_valid():
#         try:
#             statement = SEDStatement.objects.get(unique_uuid=serializer.validated_data.get('unique_uuid'))
#             if statement.verified and statement.sign_is_valid:
#                 return Response({"detail": 'already verified'}, status=status.HTTP_409_CONFLICT)
#             crypto_client = CryptoClient()
#             result = crypto_client.verify_data_data_path(data_path=statement.statement_doc.path,
#                                                          sign_data=serializer.validated_data.get('sign'))
#             if result['code'] not in (0, 8):
#                 return Response(result.get('code_message'), status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 statement.sign_is_valid = True
#                 statement.verified = True
#                 statement.sign_b64 = serializer.validated_data.get('sign')
#                 statement.verify_result = result
#                 statement.save()
#                 return Response(result)
#         except SEDStatement.DoesNotExist:
#             return Response({"detail": 'not found'}, status=status.HTTP_404_NOT_FOUND)
#
#     else:
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
#
#
# ##-------------------------------------------------------------


@swagger_auto_schema(methods=['post'], request_body=StatementInfo)
@api_view(['POST'], )
def get_statement_info(request):
    serializer = StatementInfo(data=request.data)
    if serializer.is_valid():
        try:
            statement = SEDStatement.objects.get(unique_uuid=serializer.validated_data.get('unique_uuid'))
            result = SEDStatementSerializer(instance=statement).data
            result.update({"verify_result": statement.verify_result})
            return Response(result)
        except SEDStatement.DoesNotExist:
            return Response({"detail": 'not found'}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(methods=['post'], request_body=VerifySing)
@api_view(['POST'], )
def verify_sign(request):
    from l_core.ua_sign import verify_external, get_signer_info
    serializer = VerifySing(data=request.data)
    if serializer.is_valid():
        try:
            statement = SEDStatement.objects.get(unique_uuid=serializer.validated_data.get('unique_uuid'))
            if statement.verified and statement.sign_is_valid:
                return Response({"code": 3,
                                 'code_message': 'Заява з таким номером вже успішно перевірена, зміни внести неможливо.'},
                                status=status.HTTP_409_CONFLICT)

            result = verify_external(data_path=statement.statement_doc.path,
                                     sign_data=serializer.validated_data.get('sign'))

            signer_info = get_signer_info(serializer.validated_data.get('sign'))

            if result.get('code') != 0:
                return Response(result, status=status.HTTP_400_BAD_REQUEST)

            cert_edrpou = result.get('cert').get('pszSubjEDRPOUCode')
            if len(cert_edrpou) < 8:
                return Response({'code': 1, 'code_message': 'Не допускається підпис документа фізичною особою!'},
                                status=status.HTTP_400_BAD_REQUEST)
            elif not result.get('cert').get('bTimeStamp'):
                return Response({'code': 1, 'code_message': 'Не встановлено мітку часу!'},
                                status=status.HTTP_400_BAD_REQUEST)
            elif cert_edrpou != statement.contractor.edrpou:
                return Response({'code': 1,
                                 'code_message': 'ЄДРПОУ  організації підписанта ЕЦП та організації вказаної в заяві не співпадають.'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                statement.sign_is_valid = True
                statement.verified = True
                statement.sign_b64 = serializer.validated_data.get('sign')
                statement.verify_result = result.get('cert')
                edrpou = statement.contractor.edrpou or statement.contractor.ipn
                statement.ecp_certificate = statement.save_ecp_certificate(signer_info.get('cert_data'), edrpou)
                statement.save()
                return Response(result)
        except SEDStatement.DoesNotExist:
            return Response({"detail": 'not found'}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


##-------------------------------------------------------------


automatic_number_gen = openapi.Parameter('automatic_number_gen', openapi.IN_BODY, type=openapi.TYPE_BOOLEAN)
start_date = openapi.Parameter('start_date', openapi.IN_BODY, type=openapi.TYPE_STRING)
start_of_contract = openapi.Parameter('start_of_contract', openapi.IN_BODY, type=openapi.TYPE_STRING)
expiration_date = openapi.Parameter('expiration_date', openapi.IN_BODY, type=openapi.TYPE_STRING)


@swagger_auto_schema(methods=['post'], request_body=ContractSerializer)
@api_view(['POST'])
def CreateContractFromStatement(request):

    automatic_number_gen = request.POST.get('automatic_number_gen')
    start_date = request.POST.get('start_date')
    start_of_contract = request.POST.get('start_of_contract')
    expiration_date = request.POST.get('expiration_date')
    serializer = ContractSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    contract = serializer.instance
    res = ContractSerializer(contract)
    ##Розраховуєму опарпметри договору, додаткові послуги, тарифний план, ітд
    contract.set_details_from_statement()

    return JsonResponse(res.data)
