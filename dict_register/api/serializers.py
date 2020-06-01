from __future__ import unicode_literals

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_flex_fields import FlexFieldsModelViewSet
from l_core.api.base.serializers import DynamicFieldsModelSerializer, BaseViewSetMixing
from sync_client.authentication import SyncClientAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser,AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from dict_register.models import  TemplateDocument,  Product, Subscription


class TemplateDocumentSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = TemplateDocument
        fields = ('id', '__str__', 'template_file', 'related_model_name')


# ViewSets define the view behavior.
class TemplateDocumentViewSet(BaseViewSetMixing):
    authentication_classes = [SyncClientAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TemplateDocument.objects.all()
    serializer_class = TemplateDocumentSerializer
    filterset_fields = {
        'related_model_name': ['exact']}


##-------------------------------------------------------------

##Subscription-------------------------------------------------------
class SubscriptionSerializerPrivate(DynamicFieldsModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', '__str__', 'code', 'name', 'price', 'pdv', 'price_pdv','s_count','service_type')


# ViewSets define the view behavior.
class SubscriptionPrivateViewSet(BaseViewSetMixing):
    authentication_classes = [SyncClientAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializerPrivate
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'code')
    filterset_fields = ['service_type']


##-------------------------------------------------------------


##Product-------------------------------------------------------
class ProductSerializerPrivate(DynamicFieldsModelSerializer):
    class Meta:
        model = Product
        fields = ('id', '__str__', 'code', 'name', 'price', 'pdv', 'price_pdv','product_type')


# ViewSets define the view behavior.
class ProductPrivateViewSet(BaseViewSetMixing):
    authentication_classes = [SyncClientAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Product.objects.all()
    serializer_class = ProductSerializerPrivate
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'code')
    filterset_fields = ['product_type']
##-------------------------------------------------------------
