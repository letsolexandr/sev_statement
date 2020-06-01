# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import routers, serializers, viewsets


from .api_serializer import CoreUserViewSet

router = routers.DefaultRouter()


router.register(r'user', CoreUserViewSet)## Запитання

