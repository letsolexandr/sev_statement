from django.conf.urls import url, include

from contracts import views

urlpatterns = [
    url(r'contracts/', include('contracts.api.router')),
    ##url(r'termos/', views.start)
]
