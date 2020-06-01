from django.conf.urls import url, include

urlpatterns = [
    url(r'dict/', include('dict_register.api.router_public')),
    ##url(r'dict-private/', include('dict_register.api.router_private')),
]