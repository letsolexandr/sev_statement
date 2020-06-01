from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'l_core'

    def ready(self):
        from l_core import connectors