from django.conf.urls import *
from rest_framework import routers

from .views import SEDStatemantPrivateViewSet, CreateContractFromStatement

router = routers.SimpleRouter()

router.register(r'private-sed-statement', SEDStatemantPrivateViewSet, basename='private')

urlpatterns = [
    url(r'create-contract', CreateContractFromStatement),

]


urlpatterns += router.urls
