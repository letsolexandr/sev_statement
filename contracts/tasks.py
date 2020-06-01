from __future__ import absolute_import, unicode_literals

from celery import shared_task
import time
from datetime import date

from contracts.models import RegisterAccrual, Contract, RegisterAct


@shared_task
def simulate_work():
    time.sleep(5)
    return 'task complete'


@shared_task
def calculate_accruals():
    Contract.calculate_accruals()


@shared_task
def generate_acts():
    RegisterAct.generate_acts()
