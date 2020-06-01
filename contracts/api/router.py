from django.conf.urls import *
from rest_framework import routers

from .serializers import ContractSerializerViewSet, RegisterAccrualViewSet, RegisterPaymentViewSet, RegisterActViewSet, \
    RegisterTemplateDocumentViewSet, refrashTotalBalance, calculateAccrual, clearAccrualData, StagePropertyViewSet, \
    CoordinationViewSet, generate_acts_view, PayPlanViewSet, ContractSubscriptionViewSet, calculateAccrualInRange, \
    UploadCilentBankl,UploadCilentBanklViewSet,get_accrual_zip,ConvertCilentBanklSeView,ContractProductsViewSet

router = routers.DefaultRouter()

router.register(r'contract', ContractSerializerViewSet)
router.register(r'register-accurual', RegisterAccrualViewSet)
router.register(r'register-payment', RegisterPaymentViewSet)
router.register(r'register-act', RegisterActViewSet)
router.register(r'register-template-doc', RegisterTemplateDocumentViewSet)
router.register(r'stage-property', StagePropertyViewSet)
router.register(r'coordination', CoordinationViewSet)
router.register(r'pay-plan', PayPlanViewSet)
router.register(r'contract-subscription', ContractSubscriptionViewSet)
router.register(r'contract-products', ContractProductsViewSet)
router.register(r'import-client-bank', UploadCilentBanklViewSet)

urlpatterns = [
    url(r'refresh-total-balance', refrashTotalBalance),
    url(r'calculate-accrual', calculateAccrual),
    url(r'clear-accrual-data', clearAccrualData),
    url(r'generate-acts', generate_acts_view),
    url(r'calculate-range-accrual', calculateAccrualInRange),
    url(r'upload-client-bunk', UploadCilentBankl),
    url(r'export-accrual-zip', get_accrual_zip),
    url(r'convert-client-bank', ConvertCilentBanklSeView),


]

urlpatterns += router.urls
