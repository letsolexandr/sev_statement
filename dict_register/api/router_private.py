from django.conf.urls import *
from rest_framework import routers

from .serializers import  TemplateDocumentViewSet,SubscriptionPrivateViewSet,ProductPrivateViewSet

router = routers.DefaultRouter()

router.register(r'template-document', TemplateDocumentViewSet)
router.register(r'subscription', SubscriptionPrivateViewSet)
router.register(r'product', ProductPrivateViewSet)

urlpatterns = router.urls
