"""agroscope URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls import url, include
from rest_auth.urls import PasswordResetView
from django.views.generic import TemplateView, RedirectView

schema_view = get_schema_view(
    openapi.Info(
        title='ДП "Держінфоресурс" API',
        default_version='v1',
        description='API "Держінфоресурс"',
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="letsolexandr@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    patterns=[
        url(r'api/dict/', include('dict_register.api.router_public')),
        url(r'api/statement/', include('statement.api.public_router'))
              ],
    permission_classes=(permissions.AllowAny,),
)


private_schema_view = get_schema_view(
    openapi.Info(
        title='ДП "Держінфоресурс" API',
        default_version='v1',
        description='Опис програмного інтерфесу подачі звернень на підключення  до СЕВ ОВВ',
        terms_of_service="http://dir.gov.ua/",
        contact=openapi.Contact(email="letsolexandr@gmail.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,

    permission_classes=(permissions.AllowAny,),
)


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('api/admin/', admin.site.urls),
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^private-swagger(?P<format>\.json|\.yaml)$', private_schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^private-swagger/$', private_schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    # url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path(r'api/rest-auth/', include('rest_auth.urls')),
    path(r'api/rest-auth/registration/', include('rest_registration.api.urls')),
    url(r'^password-reset/$',
        TemplateView.as_view(template_name="password_reset.html"),
        name='password-reset'),
    url(r'^password-reset/confirm/$',
        TemplateView.as_view(template_name="password_reset_confirm.html"),
        name='password-reset-confirm'),
    url(r'^user-details/$',
        TemplateView.as_view(template_name="user_details.html"),
        name='user-details'),
    url(r'^password-change/$',
        TemplateView.as_view(template_name="password_change.html"),
        name='password-change'),
    # this url is used to generate email content
    url(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        TemplateView.as_view(template_name="password_reset_confirm.html"),
        name='password_reset_confirm'),

    path(r'api/', include('l_core.urls')),
    path(r'api/', include('dict_register.urls')),
    path(r'api/', include('statement.urls')),
    path(r'api/', include('l_core.urls')),
    path('sync-client/',  include('sync_client.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path('__debug__/', include(debug_toolbar.urls)),

                      # For django versions before 2.0:
                      # url(r'^__debug__/', include(debug_toolbar.urls)),

                  ] + urlpatterns

urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]

urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + urlpatterns
