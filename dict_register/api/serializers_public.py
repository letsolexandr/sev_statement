from __future__ import unicode_literals

from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter, OrderingFilter
from l_core.api.base.serializers import DynamicFieldsModelSerializer
from rest_flex_fields import FlexFieldsModelViewSet

from dict_register.models import   Product, Subscription



##Subscription-------------------------------------------------------
class SubscriptionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Subscription
        fields = ('id', '__str__', 'code', 'name', 'price', 'pdv', 'price_pdv','s_count','service_type')


# ViewSets define the view behavior.
class SubscriptionViewSet(FlexFieldsModelViewSet):
    http_method_names = [u'get', u'options']
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'code')
    filterset_fields = ['service_type']


##-------------------------------------------------------------


##Product-------------------------------------------------------
class ProductSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Product
        fields = ('id', '__str__', 'code', 'name', 'price', 'pdv', 'price_pdv','product_type')


# ViewSets define the view behavior.
class ProductViewSet(FlexFieldsModelViewSet):
    http_method_names = [u'get', u'options']
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'code')
    filterset_fields = ['product_type']
##-------------------------------------------------------------
