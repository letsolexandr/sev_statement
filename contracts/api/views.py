import os
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
import zipfile
from l_core.api.base.serializers import BaseViewSetMixing
from .serializers import ContractSerializer, RegisterAccrualSerializer, RegisterPaymentSerializer, \
    RegisterActSerializer, ContractSubscriptionSerializer, ContractProductsSerializer, calculateAccrualSerializer, \
    UploadCilentBanklSerializer
from ..models import Contract, RegisterAccrual, RegisterPayment, RegisterAct, ContractSubscription, ContractProducts
from contracts.tasks import calculate_accruals
from django.utils.crypto import get_random_string
from django.conf import settings

MEDIA_ROOT = settings.MEDIA_ROOT
MEDIA_URL = settings.MEDIA_URL



class ContractSerializerViewSet(BaseViewSetMixing):
    """Договори"""
    permit_list_expands = ['contractor_data']
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = {
        'contractfinance__total_size_pay': ['exact', 'gte', 'lte'],
        'contractfinance__total_balance': ['exact', 'gte', 'lte'],
        'number_contract': ['exact', 'icontains'],
        'contractor': ['exact'],
        'status': ['exact'],
        'expiration_date': ['exact'],
        'start_date': ['exact']
    }
    search_fields = ('number_contract', 'contractor__full_name')
    ordering_fields = ('contractfinance__total_size_accrual',
                       'contractfinance__total_size_pay',
                       'contractfinance__total_balance',
                       'contractor__name',
                       'number_contract', 'parent_element', 'start_date', 'start_of_contract', 'start_payment',
                       'subject_contract', 'copy_contract', 'contractor', 'contractor_name', 'price_contract',
                       'contract_time', 'expiration_date')


##-------------------------------------------------------------
class RegisterAccrualViewSet(BaseViewSetMixing):
    permit_list_expands = ['contract']
    queryset = RegisterAccrual.objects.all()
    serializer_class = RegisterAccrualSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['contract__number_contract']
    filterset_fields = {
        'contract__id': ['exact'],
        'date_accrual': ['exact', 'year__exact', 'month__exact'],
    }
    ordering = ['date_accrual', 'date_sending_doc']


##-------------------------------------------------------------
class RegisterPaymentViewSet(BaseViewSetMixing):
    permit_list_expands = ['contract_data']
    queryset = RegisterPayment.objects.all()
    serializer_class = RegisterPaymentSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['contract__id']


##-------------------------------------------------------------
class RegisterActViewSet(BaseViewSetMixing):
    permit_list_expands = ['accrual', 'contract']
    queryset = RegisterAct.objects.all()
    serializer_class = RegisterActSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = {'contract': ['exact'],
                        'is_send_successful': ['exact'], }
    ordering_fields = ['date_formation_act', 'is_send_successful']
    ordering = ['date_formation_act']


class ContractSubscriptionViewSet(BaseViewSetMixing):
    queryset = ContractSubscription.objects.all()
    serializer_class = ContractSubscriptionSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['contract__id']


##-------------------------------------------------------------
class ContractProductsViewSet(BaseViewSetMixing):
    queryset = ContractProducts.objects.all()
    serializer_class = ContractProductsSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ['contract__id']
##-------------------------------------------------------------------


@api_view(['GET'])
def refrashTotalBalance(request):
    refresh_count = Contract.refresh_total_balance()
    return Response({'refresh_count': refresh_count})


@api_view(['GET'])
def generate_acts_view(request):
    generated_acts = RegisterAct.generate_acts()
    return Response({'generated_acts': generated_acts})


@api_view(['GET'])
def calculateAccrual(request):
    calculate_accruals()
    result = calculate_accruals.delay()
    return Response({'task_id': result.task_id})


@api_view(['GET'])
def clearAccrualData(request):
    from contracts.models import RegisterAccrual, RegisterAct, ContractFinance
    register_act_count = RegisterAct.objects.all().count()
    RegisterAct.objects.all().delete()
    register_accrual_count = RegisterAccrual.objects.all().count()
    RegisterAccrual.objects.all().delete()
    ContractFinance.objects.all().update(last_date_accrual=None,
                                         total_size_accrual=0, last_date_pay=None, total_size_pay=0, total_balance=0)
    return Response({'register_accrual_count': register_accrual_count, "register_act_count": register_act_count})


@api_view(['POST'])
def calculateAccrualInRange(request):
    serializer = calculateAccrualSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        from contracts.models import Contract
        res = Contract.calculate_accruals(**data)

        return Response(res)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadCilentBanklViewSet(BaseViewSetMixing):
    from contracts.models import ImportPayment
    queryset = ImportPayment.objects.all()
    serializer_class = UploadCilentBanklSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)


@api_view(['POST'])
def UploadCilentBankl(request):
    serializer = UploadCilentBanklSerializer(data=request.data)
    if serializer.is_valid():
        res = serializer.save()
        return Response(res.details)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_accrual_zip(request):
    _ids = request.GET.getlist('ids[]')
    ids = [int(item) for item in _ids]
    base_name = get_random_string() + '.zip'
    mk_path = os.path.join(MEDIA_ROOT, 'tmp')

    if not os.path.exists(mk_path):
        os.makedirs(mk_path)

    zf_path = os.path.join(MEDIA_ROOT, 'tmp', base_name)
    zf = zipfile.ZipFile(zf_path, "w")
    print(_ids, ids)
    accruals = RegisterAccrual.objects.filter(pk__in=ids).values('accrual_docx')

    for accrual in accruals:
        print('Accrual:', accrual['accrual_docx'])
        zf.write(os.path.join(MEDIA_ROOT, accrual['accrual_docx']), os.path.basename(accrual['accrual_docx']))
    zf.close()

    url = os.path.join(MEDIA_URL, 'tmp', base_name)
    return Response({'url': url})
