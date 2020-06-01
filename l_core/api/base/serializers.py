# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from typing import Dict, List, AnyStr
import json

from django_filters import rest_framework as filters
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import serializers, viewsets
from rest_framework.decorators import api_view
from django.apps import apps

from rest_framework.exceptions import APIException
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from rest_flex_fields import FlexFieldsModelViewSet, FlexFieldsModelSerializer

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from l_core.models import CoreUser, Group, CoreOrganization, GroupOrganization, AdminSettings

import logging
from django.http.request import HttpRequest

logger = logging.getLogger(__name__)


class UserViewMixing(object):
    """Додає автора та редактора при збереженні"""

    def perform_create(self, serializer):
        if self.request.user:
            try:
                serializer.save(author=self.request.user)
            except Exception as e:
                logger.error(e)
                serializer.save()

    def perform_update(self, serializer):
        if self.request.user:
            try:
                serializer.save(editor=self.request.user)
            except Exception as e:
                logger.error(e)
                serializer.save()


class BaseViewSetMixing(UserViewMixing, FlexFieldsModelViewSet):
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        mode = request.GET.get('mode')
        self.perform_destroy(instance, mode)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance, mode=None):
        ##raise Exception
        instance.delete(mode=mode)


class LCorePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def display_value(self, instance):
        return instance.natural_key

    def to_representation(self, value):
        return value.natural_key


class DynamicFieldsModelSerializer(FlexFieldsModelSerializer):
    """
    A ModelSerializer that takes an additional `fields` argument that
    controls which fields should be displayed.
    """

    def __init__(self, *args, **kwargs):
        # Instantiate the superclass normally
        ##print('__init__')

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)
        self.set_write_only_fields()

    def _clean_fields(self, omit_fields, sparse_fields, next_level_omits):
        f = self.fields

        ##logger.debug('_clean_fields')

        super(DynamicFieldsModelSerializer, self)._clean_fields(omit_fields, sparse_fields, next_level_omits)

    def set_write_only_fields(self):
        meta = self.Meta
        if hasattr(meta, 'write_only_fields'):
            write_only_fields = self.Meta.write_only_fields

            for field in self.fields.values():
                if field.field_name in write_only_fields:
                    field.write_only = True
                    print(field.field_name)

    def get_field_names(self, declared_fields, info):
        ##print('get_field_names')
        request = self.context.get('request')
        if request:
            fields_ext = self.context['request'].query_params.get('fields')
        else:
            fields_ext = None

        if fields_ext:
            fields_ext = fields_ext.split(',')
        else:
            fields_ext = []
        fields = super(DynamicFieldsModelSerializer, self).get_field_names(declared_fields, info)
        result_list = list(set(fields_ext) | set(fields))
        ##logger.debug('get_field_names')
        return result_list

    def get_uniqueness_extra_kwargs(self, field_names, declared_fields, extra_kwargs):
        ##print('get_uniqueness_extra_kwargs')
        fields = super(DynamicFieldsModelSerializer, self).get_uniqueness_extra_kwargs(field_names, declared_fields,
                                                                                       extra_kwargs)
        ##logger.debug('get_uniqueness_extra_kwargs')
        return fields

    def build_property_field(self, field_name, model_class):
        ##print('build_property_field')
        field_class, field_kwargs = super(DynamicFieldsModelSerializer, self).build_property_field(field_name,
                                                                                                   model_class)
        ##logger.debug('build_property_field')
        return field_class, field_kwargs


##CoreUser-------------------------------------------------------
class CoreUserSerializer(DynamicFieldsModelSerializer, serializers.ModelSerializer):
    org_name = serializers.SerializerMethodField(method_name='orgname')

    ##user_permissions_items = serializers.SerializerMethodField()
    class Meta:
        model = CoreUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'groups', 'user_permissions',  ##'user_permissions_items',
                  'organization', 'org_name', '__str__', 'related_objects')

    def orgname(self, obj):
        return obj.organization.__str__() if obj.organization else None

    def get_user_permissions_items(self, obj):
        data = []
        unicode_ids = []
        for item in Permission.objects.all():
            if item.id not in unicode_ids:
                unicode_ids.append(item.id)
                data.append({'id': item.id, 'name': item.name})
        return data


# ViewSets define the view behavior.
class CoreUserViewSet(viewsets.ModelViewSet):
    queryset = CoreUser.objects.all()
    serializer_class = CoreUserSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('first_name', 'last_name', 'organization__name')


##-------------------------------------------------------------


##CoreUserGroup-------------------------------------------------------
class CoreUserGroupSerializer(serializers.ModelSerializer):
    related_objects = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('name', '__str__', 'id', 'permissions', 'related_objects')

    def __str__(self):
        return self.name

    def get_related_objects(self, obj):
        """Повертає список повязаних обєктів"""
        related_fields = obj._meta.related_objects
        related_list = []
        for related in related_fields:
            field_name = related.get_cache_name()
            if hasattr(obj, field_name):
                related_field = getattr(obj, field_name)
                if hasattr(related_field, 'all'):
                    queryset = related_field.all()
                    children = []
                    name = None
                    for item in queryset:
                        name = item._meta.verbose_name_plural
                        children.append({'id': item.id, 'name': str(item)})

                    if name:
                        data = {'name': name, 'id': obj.id, 'children': children}
                        related_list.append(data)
                else:
                    data = {'name': str(related_field), 'id': related_field.id}
                    related_list.append(data)
        return related_list


# ViewSets define the view behavior.
class CoreUserGroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = CoreUserGroupSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name',)
    filter_fields = ('id',)


##-------------------------------------------------------------


##ContentType-------------------------------------------------------
class ContentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = ('app_label', 'model', '__str__', 'id',)


# ViewSets define the view behavior.
class ContentTypeViewSet(viewsets.ModelViewSet):
    queryset = ContentType.objects.all()
    serializer_class = ContentTypeSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('app_label', 'model')


##-------------------------------------------------------------
##Permissions-------------------------------------------------------
class PermissionsSerializer(DynamicFieldsModelSerializer):
    content_type_data = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Permission
        fields = ('name', 'content_type', 'content_type_data', 'codename', '__str__', 'id',)
        expandable_fields = {
            'content_type_data': (
                ContentTypeSerializer, {'source': 'content_type', })
        }

    def __str__(self):
        return self.name


# ViewSets define the view behavior.
class PermissionsViewSet(BaseViewSetMixing):
    permit_list_expands = ['content_type_data']
    queryset = Permission.objects.all()
    serializer_class = PermissionsSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'codename')


##-------------------------------------------------------------


##CoreOrganization-------------------------------------------------------
class CoreOrganizationSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = CoreOrganization
        fields = (
            'name', 'full_name', 'address', 'edrpou', 'phone', 'fax', 'email', 'site', 'work_reason',
            'group_organization', '__str__', 'id', 'status', 'register_date', 'sert_name',
            'main_unit', 'main_unit_state', 'main_activity', 'main_activity_text', 'settlement_account',
            'organization_type','fiz_first_name','fiz_last_name','fiz_middle_name','passport','issuer','issue_date',
            'property_type', 'note', 'mfo', 'certificate_number', 'bank_name', 'bank', 'ipn', 'statute_copy')


# ViewSets define the view behavior.
class CoreOrganizationViewSet(BaseViewSetMixing):
    queryset = CoreOrganization.objects.all()
    serializer_class = CoreOrganizationSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ['full_name', 'address', 'edrpou']
    filterset_fields = ['bank']


##-------------------------------------------------------------


##GroupOrganization-------------------------------------------------------
class GroupOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupOrganization
        fields = ('name', '__str__', 'id')


# ViewSets define the view behavior.
class GroupOrganizationViewSet(viewsets.ModelViewSet):
    queryset = GroupOrganization.objects.all()
    serializer_class = GroupOrganizationSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name')


##-------------------------------------------------------------


##AdminSettings-------------------------------------------------------
class AdminSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminSettings
        fields = ('name', 'data', 'group', '__str__', 'id')


# ViewSets define the view behavior.
class AdminSettingsViewSet(viewsets.ModelViewSet):
    queryset = AdminSettings.objects.all()
    serializer_class = AdminSettingsSerializer
    filter_backends = (filters.DjangoFilterBackend, SearchFilter, OrderingFilter)
    search_fields = ('name', 'group')


##-------------------------------------------------------------


@api_view(['GET'])
def GetUserPermissions(request):
    user = request.user
    ##from l_core.model_details import CoreUser
    ##user = CoreUser.objects.get(pk=3)
    _permissions = user.get_all_permissions()
    ##Permission.objects.filter(user=user).values('id', 'codename')
    permissions = [perm.split('.')[1] for perm in _permissions]
    return JsonResponse({'permissions': permissions,
                         'user': CoreUser.objects.filter(id=user.id).values()[0],
                         })


app_label = openapi.Parameter('app_label', openapi.IN_QUERY, description="Name of application",
                              type=openapi.TYPE_STRING, required=True)
model = openapi.Parameter('model', openapi.IN_QUERY, description=" data model", type=openapi.TYPE_STRING, required=True)
method = openapi.Parameter('method', openapi.IN_QUERY, description="method to call", type=openapi.TYPE_STRING,
                           required=True)
pk = openapi.Parameter('pk', openapi.IN_QUERY, description="object primary key", type=openapi.TYPE_INTEGER)
params = openapi.Parameter('params', openapi.IN_QUERY, description="stringify params pass to method",
                           type=openapi.TYPE_STRING)


@swagger_auto_schema(method='get', manual_parameters=[app_label, model, method, pk, params])
@api_view(['GET'])
def RPC(request):
    model_name = request.GET.get('model')
    app_label = request.GET.get('app_label')
    model_method = request.GET.get('method')
    _params = request.GET.get('params')
    params = json.loads(_params) if _params else None
    pk = request.GET.get('pk')
    model = apps.get_model(app_label=app_label, model_name=model_name)
    result = {}
    if pk:
        obj = model.objects.get(pk=pk)
        if hasattr(obj, model_method):
            method = getattr(obj, model_method)

            if params:
                result['data'] = method(params)
            else:
                result['data'] = method()

            result['status'] = 'success'
        else:
            result['status'] = 'error'
            result['message'] = 'method "{}" is not exist '.format(model_method)

    else:
        if hasattr(model, model_method):
            class_method = getattr(model, model_method)

            if params:
                result['data'] = class_method(params)
            else:
                result['data'] = class_method()
            result['status'] = 'success'
        else:
            result['status'] = 'error'
            result['message'] = 'class method "{}" is not exist '.format(model_method)

    return JsonResponse({'result': result})


##########################################################################################

ids = openapi.Parameter('ids[]', openapi.IN_QUERY, description="list of ids", type=openapi.TYPE_ARRAY,
                        items=openapi.Items(type=openapi.TYPE_INTEGER))
request_q = openapi.Parameter('request_q', openapi.IN_QUERY, description="list of ids", type=openapi.TYPE_OBJECT)
delete_all_in_query = openapi.Parameter('delete_all_in_query', openapi.IN_QUERY, description="list of ids",
                                        type=openapi.TYPE_BOOLEAN)


@swagger_auto_schema(method='get', manual_parameters=[app_label, model, request_q, ids, delete_all_in_query])
@api_view(['GET'])
def MultipleDelete(request: HttpRequest):
    result = {}
    model_name = request.GET.get('model')
    if not model_name:
        raise APIException('"model_name" is required!')

    app_label = request.GET.get('app_label')
    if not app_label:
        raise APIException('"app_label" is required!')
    ##request_q: Dict = json.loads(request.GET.get('request_q'))
    request_q: Dict = {}
    delete_all_in_query: bool = json.loads(request.GET.get('delete_all_in_query', 'false'))
    _ids = request.GET.getlist('ids[]')
    ids = [int(item) for item in _ids]
    if not delete_all_in_query:
        request_q.update({"pk__in": ids})
    model = apps.get_model(app_label=app_label, model_name=model_name)
    queryset = model.objects.filter(**request_q)
    result['delete_count'] = queryset.count()
    result['status'] = 'success'
    result['status_ua'] = 'Успішно'
    result['message'] = f'Успішно видадено {result["delete_count"]} записів'
    queryset.delete()
    ##raise Exception
    return JsonResponse({'result': result})


@api_view(['GET'])
def GetRelatedObjects(request):
    obj_id = (request.GET.get('id', 0))
    if not obj_id:
        raise APIException('"obj_id" is required!')
    model_name = request.GET.get('model_name')
    if not model_name:
        raise APIException('"model_name" is required!')

    app_label = request.GET.get('app_label')
    if not app_label:
        raise APIException('"app_label" is required!')

    model = apps.get_model(app_label=app_label, model_name=model_name)
    obj = model.objects.get(pk=(obj_id))
    name = obj._meta.verbose_name
    related_fields = obj._meta.related_objects
    related_list = []
    for related in related_fields:
        field_name = related.get_cache_name()
        if hasattr(obj, field_name):
            related_field = getattr(obj, field_name)
            if hasattr(related_field, 'all'):
                queryset = related_field.all()
                for item in queryset:
                    related_list.append({'id': item.id, 'name': str(item)})
            else:
                related_list.append(str(related_field))
    return JsonResponse({'name': name, 'id': obj_id, 'children': related_list})
