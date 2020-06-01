from django.contrib.gis.db import models
import uuid
##from django.db.model_details import query
##from django.db.model_details.deletion import Collector
##from django.contrib.admin.utils import NestedObjects
from django.forms.models import model_to_dict
from .mixins import CheckProtected, RelatedObjects


class SoftDeleteManager(models.Manager):
    MODE_CHOISE = ['clear', 'deleted', 'all']

    def __init__(self, *args, **kwargs):
        mode = kwargs.pop('mode', 'clear')
        ##raise Exception(mode)
        if not mode:
            raise Exception('"mode" is required in "SoftDeleteManager"')

        if mode not in SoftDeleteManager.MODE_CHOISE:
            raise Exception('"mode" must bee in  "SoftDeleteManager.MODE_CHOISE"')
        super(SoftDeleteManager, self).__init__(*args, **kwargs)
        self.mode = mode

    def get_queryset(self):
        base_qeeryset = super(SoftDeleteManager, self).get_queryset()
        ##base_qeeryset = SafeDeleteQueryset(self.model, using=self._db)

        if self.mode == 'clear':
            qs = base_qeeryset.filter(is_deleted=False)
        elif self.mode == 'deleted':
            qs = base_qeeryset.filter(is_deleted=True)
        elif self.mode == 'all':
            qs = base_qeeryset.all()
        else:
            raise Exception('"mode" not set')

        return qs


class AbstractBase(CheckProtected, RelatedObjects, models.Model):
    is_deleted = models.BooleanField(null=False, default=False)
    unique_uuid = models.UUIDField(default=uuid.uuid4)
    objects = SoftDeleteManager(mode='clear')
    deleted_objects = SoftDeleteManager(mode='deleted')
    objects_with_deleted = SoftDeleteManager(mode='all')

    class Meta:
        abstract = True

    def delete(self, **kwargs):
        MODE_VALUES = ['hard', 'soft']

        mode = kwargs.pop('mode', 'hard')
        if not mode:
            mode = 'hard'

        if mode not in MODE_VALUES:
            raise Exception('"mode" in "{}"'.format(','.join(MODE_VALUES)))
        ##self.delete_related_objects(mode=mode)
        if mode == 'soft':
            self.soft_delete()
        else:
            self.hard_delete()

    def hard_delete(self):
        super(AbstractBase, self).delete()

    def soft_delete(self):
        self.is_deleted = True
        self.save()

    def restore(self):
        self.is_deleted = False
        self.save()

    def delete_related_objects(self, mode=None):
        """ Видаляє поваязані обєкти """
        obj = self
        related_fields = obj._meta.related_objects
        for related in related_fields:
            field_name = related.get_cache_name()
            if hasattr(obj, field_name):
                related_field = getattr(obj, field_name)
                if hasattr(related_field, 'all'):
                    queryset = related_field.all()
                    for item in queryset:
                        item.delete(mode=mode)
                else:
                    related_field.delete(mode=mode)

    def as_dict(self, fields):
        return model_to_dict(self, fields=fields or [field.name for field in self._meta.fields])

    @property
    def natural_key(self):
        return {'id': self.id, 'value': self.__str__()}
