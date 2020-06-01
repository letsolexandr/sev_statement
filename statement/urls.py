from django.conf.urls import url, include
from django.urls import path
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

# public_statement_schema_view = get_schema_view(
#     openapi.Info(
#         title='ДП "Держінфоресурс" API',
#         default_version='v1',
#         description='Опис програмного інтерфесу подачі звернень на підключення Центрів надання адміністративних послуг  ПК ЦНАП до СЕВ ОВВ та («Вулик»)',
#         terms_of_service="http://dir.gov.ua/",
#         contact=openapi.Contact(email="letsolexandr@gmail.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     ##patterns=[url(r'statement/', urls_data[0])],
#     patterns=[url(r'statement-public/', include('statement.api.public_router'))],
#     permission_classes=(permissions.IsAuthenticatedOrReadOnly, permissions.DjangoModelPermissions,),
# )
#
# statement_schema_view = get_schema_view(
#     openapi.Info(
#         title='ДП "Держінфоресурс" API',
#         default_version='v1',
#         description='Опис програмного інтерфесу подачі звернень на підключення Центрів надання адміністративних послуг  ПК ЦНАП до СЕВ ОВВ та («Вулик»)',
#         terms_of_service="http://dir.gov.ua/",
#         contact=openapi.Contact(email="letsolexandr@gmail.com"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     patterns=[url(r'statement/', include('statement.api.router'))],
#     permission_classes=(permissions.IsAuthenticatedOrReadOnly, permissions.DjangoModelPermissions,),
# )

urlpatterns = [
    url(r'statement/', include('statement.api.public_router')),
    url(r'private-statement/', include('statement.api.router')),
    # url(r'^statement/doc/public$', public_statement_schema_view.with_ui('swagger', cache_timeout=0),
    #     name='statement-public-schema-swagger-ui'),
    # url(r'^statement/doc/private', statement_schema_view.with_ui('swagger', cache_timeout=0),
    #     name='statement-schema-swagger-ui'),
    ##url(r'termos/', views.start)
]
