from .router_public import urlpatterns as public_urlpatterns
from .router_private import urlpatterns as private_urlpatterns

urlpatterns = public_urlpatterns + private_urlpatterns
