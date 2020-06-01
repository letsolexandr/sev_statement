# -*- coding: utf-8 -*-

from django.conf.urls import *
from rest_framework import routers

from .serializers import (CoreUserViewSet, CoreUserGroupViewSet, CoreOrganizationViewSet,
                          GroupOrganizationViewSet, GetUserPermissions, AdminSettingsViewSet, GetRelatedObjects, RPC,
                          MultipleDelete,PermissionsViewSet,ContentTypeViewSet)
from .views import validate_email

router = routers.DefaultRouter()

router.register(r'user', CoreUserViewSet)
router.register(r'group', CoreUserGroupViewSet)
router.register(r'permission', PermissionsViewSet)
router.register(r'content-type', ContentTypeViewSet)
router.register(r'organization', CoreOrganizationViewSet)
router.register(r'group-organization', GroupOrganizationViewSet)
router.register(r'admin-settings', AdminSettingsViewSet)

urlpatterns = [
    url(r'user-permissions', GetUserPermissions),
    url(r'get-related-objects', GetRelatedObjects),
    url(r'rpc', RPC),
    url(r'multiple-delete', MultipleDelete),
    url(r'validate-email', validate_email)

]

urlpatterns += router.urls
