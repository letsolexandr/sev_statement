# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from l_core.abstract_base import AbstractBase


##from django.utils.timezone import now
##from django.contrib.postgres.fields import JSONField


class DictBase(AbstractBase):
    parent = models.ForeignKey('self', null=True,blank=True, on_delete=models.SET_NULL)
    is_group = models.BooleanField(default=False)
    code = models.CharField(max_length=50, blank=True, null=True, verbose_name="Код")
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name="Значення")
    protected = models.BooleanField(default=False, verbose_name='Захищено від видалення')
    date_add = models.DateTimeField(auto_now_add=True, null=True, editable=False)
    date_edit = models.DateTimeField(auto_now=True, null=True, editable=False)
    author = models.ForeignKey('l_core.CoreUser', related_name='%(class)s_author', null=True, editable=False,
                               on_delete=models.PROTECT)
    editor = models.ForeignKey('l_core.CoreUser', related_name='%(class)s_editor', null=True, editable=False,
                               on_delete=models.PROTECT)

    class Meta:
        abstract = True
        unique_together = ['code']

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0} {1}'.format(self.code or '-', self.name or '-')

    def delete(self, **kwargs):
        if self.protected:
            raise Exception("Об'єкт захищено від видалення ! ")
        super(DictBase, self).delete(**kwargs)


class MainActivity(DictBase):
    class Meta:
        verbose_name = u'Вид основної діяльності'


class OrganizationType(DictBase):
    class Meta:
        verbose_name = u'Типів органцізації'


class PropertyType(DictBase):
    class Meta:
        verbose_name = u'Тип власності'


class ContractStatus(DictBase):
    class Meta:
        verbose_name = u'Статус договору'


class Product(DictBase):
    UNIT_CHOICES = [
        ['service', 'Послуга'],
        ['product', 'ТОвар'],
    ]

    MAIN = 'main'
    ADDITIONAL = 'additional'
    PRODUCT_TYPE_CHOICES = [
        [MAIN, 'Головна'],
        [ADDITIONAL, 'Додаткова'],
    ]

    price = models.FloatField(verbose_name="Ціна")
    pdv = models.FloatField(verbose_name="ПДВ")
    product_type = models.CharField(verbose_name="",  max_length=100, default=ADDITIONAL,choices=PRODUCT_TYPE_CHOICES)
    unit = models.CharField(verbose_name="Одиничі виміру", choices=UNIT_CHOICES, max_length=100)
    price_pdv = models.FloatField(verbose_name="Ціна з ПДВ")

    class Meta:
        verbose_name = u'Послуги,Товари'

    def __str__(self):
        return self.name


class Subscription(DictBase):
    UNIT_CHOICES = [
        ['mb', 'Мегабайти'],
    ]
    SERVICE_TYPE = [
        ['web', 'Веб-доступ'],
        ['integration', 'Інтеграція'],
    ]
    service_type = models.CharField(max_length=100, choices=SERVICE_TYPE, default='web', verbose_name="Тип послуги")
    price = models.FloatField(verbose_name="Ціна")
    pdv = models.FloatField(verbose_name="ПДВ")
    price_pdv = models.FloatField(verbose_name="Ціна з ПДВ")
    unit = models.CharField(verbose_name="Одиничі виміру", choices=UNIT_CHOICES, max_length=100,
                            default=UNIT_CHOICES[0][0])
    s_count = models.FloatField(null=True, verbose_name="Кількість ")

    class Meta:
        verbose_name = u'Обслуговування, абонплата'

    def __str__(self):
        return self.name


class TemplateDocument(DictBase):
    template_file = models.FileField(upload_to='uploads/doc_templates/%Y/%m/%d/', null=True,
                                     verbose_name="Шаблон документу")
    related_model_name = models.CharField(unique=True, max_length=100,
                                          verbose_name="Шаблон документу",
                                          null=True)

    class Meta:
        verbose_name = u'Шаблон документу'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0}'.format(self.related_model_name or '-', )
