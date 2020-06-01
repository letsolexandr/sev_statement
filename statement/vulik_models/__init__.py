
from django.db import models
from l_core.models import CoreBase
from .base import ConnectionCNAPStatement as baseConnectionCNAPStatement

VULIK_DB_NAME = 'vulik_statement'

class VulikManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().using(VULIK_DB_NAME)

class DBRouting(CoreBase):
    def save(self, *args, **kwargs):
        super(DBRouting, self).save(*args, using=VULIK_DB_NAME, **kwargs)

    def delete(self, **kwargs):
        super(DBRouting, self).delete(using=VULIK_DB_NAME,**kwargs)


class ConnectionCNAPStatement(baseConnectionCNAPStatement):
    class Meta:
        managed=False
    objects = VulikManager()