# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import AbstractUser, PermissionsMixin, Group
from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from .abstract_base import AbstractBase
from .mixins import RelatedObjects, CheckProtected
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator

default_permissions = (
    ("add", "edit", "delete", "view", "can_view_self")
)


class GroupOrganization(AbstractBase):
    name = models.CharField(max_length=200, blank=True, null=True, verbose_name=u'Назва')

    class Meta:
        verbose_name = u'Група компаній (організацій)'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0}'.format(self.name)


class FizSubject(models.Model):
    ipn = models.CharField(max_length=200, blank=True, null=True, verbose_name="індивідуальний податковий номер")
    fiz_first_name = models.TextField(blank=True, null=True, verbose_name="Імя")
    fiz_last_name = models.TextField(blank=True, null=True, verbose_name="Прізвище")
    fiz_middle_name = models.TextField(blank=True, null=True, verbose_name="По-батькові")
    passport = models.TextField(blank=True, null=True, verbose_name="Серія та номер паспорта, або ІД картки")
    issuer = models.TextField(blank=True, null=True, verbose_name="Ким виданий")
    issue_date = models.DateField(blank=True, null=True, verbose_name="Коли виданий")

    class Meta:
        abstract = True

class CoreOrganization(FizSubject,AbstractBase):
    BANK = (('K', 'Комерційний'), ('Б', 'Бюджет'))
    name = models.TextField(blank=True, null=True, verbose_name="Назва організації")
    full_name = models.TextField(blank=True, null=True, verbose_name="Повна назва організації")
    address = models.CharField(max_length=200, blank=True, null=True, verbose_name="Адреса")
    edrpou = models.CharField(max_length=50, blank=True, null=True, unique=False, verbose_name="ЄДРПОУ")
    mfo = models.CharField(max_length=50, blank=True, null=True, verbose_name="МФО")
    phone = models.CharField(max_length=200, blank=True, null=True, verbose_name="Телефон")
    fax = models.CharField(max_length=200, blank=True, null=True, verbose_name="Факс")
    email = models.EmailField(max_length=200, blank=True, null=True, verbose_name="EMAIL")
    site = models.URLField(max_length=200, blank=True, null=True, verbose_name="Сайт")
    status = models.CharField(max_length=50, blank=True, null=True, verbose_name="Статус")
    register_date = models.DateField(blank=True, null=True, verbose_name="Дата державної реєстрації")
    work_reason= models.TextField(null=True, verbose_name="Працює на підставі")
    sert_name = models.CharField(max_length=200, blank=True, null=True,
                                 verbose_name="Серія та номер державної реєстрації")
    settlement_account = models.CharField(max_length=30, blank=True, null=True, verbose_name="Розрахунковий рахунок")
    bank = models.CharField(choices=BANK, verbose_name="Тип банку", null=True, max_length=1)
    bank_name = models.CharField(max_length=200, verbose_name="Назва банку", null=True)
    taxation_method = models.CharField(max_length=200, blank=True, null=True, verbose_name="Спосіб оподаткування")
    certificate_number = models.CharField(max_length=200, blank=True, null=True, verbose_name="Номер свідотства ПДВ")
    main_unit = models.CharField(max_length=200, blank=True, null=True, verbose_name="Уповноважена особа")
    main_unit_state = models.CharField(max_length=200, blank=True, null=True, verbose_name="Посада уповноваженої особи")
    main_activity = models.ForeignKey('dict_register.MainActivity', null=True, blank=True,
                                      verbose_name=u'Основна діяльність', on_delete=models.PROTECT)
    main_activity_text = models.CharField(max_length=200, null=True, blank=True,
                                          verbose_name=u'Основна діяльність (text)')
    organization_type = models.ForeignKey('dict_register.OrganizationType', null=True, blank=True,
                                          verbose_name=u'Тип організації', on_delete=models.PROTECT)
    property_type = models.ForeignKey('dict_register.PropertyType', null=True, blank=True,
                                      verbose_name=u'Тип організації', on_delete=models.PROTECT)
    group_organization = models.ForeignKey(GroupOrganization, null=True,
                                           on_delete=models.PROTECT, verbose_name=u'Група компаній')
    central_office = models.PointField(null=True, verbose_name=u'Центральний офіс')
    statute_copy = models.FileField(null=True, verbose_name="Статутні документи",
                                    validators=[
                                        FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg'])])
    note = models.TextField(blank=True, null=True, verbose_name="Примітка")
    author = models.ForeignKey('l_core.CoreUser', related_name='%(class)s_author', null=True, editable=False,
                               on_delete=models.PROTECT)
    editor = models.ForeignKey('l_core.CoreUser', related_name='%(class)s_editor', null=True, editable=False,
                               on_delete=models.PROTECT)

    class Meta:
        verbose_name = u'Контрагент'

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return '{0} {1}'.format(self.name or self.full_name, self.edrpou or '')


class CoreUser(RelatedObjects, CheckProtected, AbstractUser):
    organization = models.ForeignKey(CoreOrganization, null=True, on_delete=models.PROTECT)
    first_name = models.CharField(_('first name'), max_length=30, blank=False)
    last_name = models.CharField(_('last name'), max_length=150, blank=False)
    email = models.EmailField(_('email address'), blank=False)

    class Meta:
        verbose_name = u'Користувач'
        verbose_name_plural = u'Користувачі'


class CoreBase(AbstractBase):
    date_add = models.DateTimeField(auto_now_add=True, null=True, editable=False)
    date_edit = models.DateTimeField(auto_now=True, null=True, editable=False)
    author = models.ForeignKey(CoreUser, related_name='%(class)s_author', null=True, editable=False,
                               on_delete=models.PROTECT)
    editor = models.ForeignKey(CoreUser, related_name='%(class)s_editor', null=True, editable=False,
                               on_delete=models.PROTECT)
    organization = models.ForeignKey(CoreOrganization, null=True, on_delete=models.PROTECT)
    is_deleted = models.BooleanField(null=False, default=False, editable=False)

    def save(self, *args, **kwargs):
        super(CoreBase, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class Counter(models.Model):
    max_value = models.IntegerField(default=0)
    model = models.CharField(max_length=100)

    @classmethod
    def next_id(cls, model):
        cls.dispatch(model)
        counter_obj = cls.objects.filter(model=model)[0]
        next_id = counter_obj.max_value + 1
        counter_obj.max_value = next_id
        counter_obj.save()
        return next_id

    @classmethod
    def dispatch(cls, model):
        if cls.objects.filter(model=model).count() == 0:
            cls.objects.create(model=model)
            ##print('Create counter:', model)


class AdminSettings(CoreBase):
    GROUPS = [('report', u'Звіти')]
    name = models.CharField(max_length=100)
    group = models.CharField(max_length=100, choices=GROUPS)
    data = JSONField()

    class Meta:
        unique_together = [['name']]

    def save(self, *args, **kwargs):
        super(AdminSettings, self).save(*args, **kwargs)
