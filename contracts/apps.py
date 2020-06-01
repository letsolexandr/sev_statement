from django.apps import AppConfig


class ContractsConfig(AppConfig):
    name = 'contracts'

    def ready(self):
        from contracts import connectors