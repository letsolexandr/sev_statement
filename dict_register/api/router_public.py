from django.conf.urls import *
from rest_framework import routers

from .serializers_public import SubscriptionViewSet,ProductViewSet

router = routers.DefaultRouter()


router.register(r'subscription', SubscriptionViewSet)
router.register(r'product', ProductViewSet)

urlpatterns = router.urls
