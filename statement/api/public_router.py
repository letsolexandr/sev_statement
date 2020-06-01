from django.conf.urls import *
from rest_framework import routers

from .views import SEDStatemantViewSet, create_pdf_integration_statement,create_pdf_web_statement, verify_sign,get_statement_info

router = routers.SimpleRouter()

router.register(r'sed-statement', SEDStatemantViewSet,basename='public')



urlpatterns = [
    url(r'integration-statement', create_pdf_integration_statement),
    url(r'web-access-statement', create_pdf_web_statement),
    url(r'statement-verify', verify_sign),
    url(r'statement-info', get_statement_info),
    url(r'statement-info', get_statement_info),

]

urlpatterns += router.urls
