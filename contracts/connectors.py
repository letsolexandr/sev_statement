from django.db.models import signals
from contracts.models import RegisterAct, ContractFinance, Contract, RegisterAccrual, RegisterPayment, StageProperty, \
    PayPlan, ContractProducts, ContractSubscription


def create_act(sender, instance, created, **kwargs):

    instance.contract.refresh_balance()



def post_delete_act(sender, instance: RegisterAct, **kwargs):
    if instance.contract:
        instance.contract.refresh_balance()


def create_update_payment(sender, instance, created, **kwargs):
    instance.contract.refresh_balance()


def delete_payment(sender, instance, **kwargs):
    instance.contract.refresh_balance()


def create_update_accrual(sender, instance, created, **kwargs):
    instance.contract.refresh_balance()

def create_update_accrual(sender, instance, created, **kwargs):
    instance.contract.refresh_balance()

def create_update_contract(sender, instance, created, **kwargs):
    if not created:
        contracts_finance = ContractFinance.objects.filter(contract=instance)
        if contracts_finance.count() > 0:
            finance = contracts_finance[0]
            finance.set_finance_values()
            finance.save()
        else:
            finance = ContractFinance(contract=instance)
            finance.set_finance_values()
            finance.save()
    else:
        ##
        finance = ContractFinance(contract=instance)
        finance.set_finance_values()
        finance.save()
        ### save satage_propery
        satage_propery = StageProperty()
        satage_propery.contract = instance
        satage_propery.load_from_statemant()
        satage_propery.save()
        ## Сформувати проект договору
        ##instance.generate_doc(save_in_contract=True)
        ## save satage_propery


signals.post_save.connect(receiver=create_update_contract, sender=Contract)
signals.post_save.connect(receiver=create_update_accrual, sender=RegisterAccrual)
signals.post_save.connect(receiver=create_update_payment, sender=RegisterPayment)
signals.post_delete.connect(receiver=delete_payment, sender=RegisterPayment)
signals.post_save.connect(receiver=create_act, sender=RegisterAccrual)
signals.post_delete.connect(receiver=post_delete_act, sender=RegisterAct)
signals.post_save.connect(receiver=create_update_ContractXXX, sender=ContractSubscription)
signals.post_save.connect(receiver=create_update_ContractXXX, sender=ContractProducts)
signals.post_delete.connect(receiver=delete_ContractXXX, sender=ContractSubscription)
signals.post_delete.connect(receiver=delete_ContractXXX, sender=ContractProducts)
