import string
import random
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from .models import AvailableCash, Loan, Payment, Transfer

def generate_unique_loan_id():
    while True:
        loan_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Loan.objects.filter(loan_id=loan_id).exists():
            return loan_id

@receiver(pre_save, sender=Loan)
def set_unique_loan_id(sender, instance, **kwargs):
    if not instance.loan_id:
        instance.loan_id = generate_unique_loan_id()


@receiver(pre_save, sender=Loan)
def capture_old_loan_amount(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_amount = Loan.objects.get(pk=instance.pk).amount
        except Loan.DoesNotExist:
            instance._old_amount = None
    else:
        instance._old_amount = None


@receiver(post_save, sender=Loan)
def adjust_available_cash_on_loan_save(sender, instance, created, **kwargs):
    if created:
        AvailableCash.adjust(-instance.amount)
        return
    old_amount = getattr(instance, '_old_amount', None)
    if old_amount is None:
        return
    AvailableCash.adjust(-(instance.amount - old_amount))


@receiver(post_delete, sender=Loan)
def restore_available_cash_on_loan_delete(sender, instance, **kwargs):
    AvailableCash.adjust(instance.amount)


@receiver(post_save, sender=Payment)
def adjust_available_cash_on_payment_save(sender, instance, created, **kwargs):
    if created:
        AvailableCash.adjust(instance.loan.monthly_payment)


@receiver(post_delete, sender=Payment)
def adjust_available_cash_on_payment_delete(sender, instance, **kwargs):
    AvailableCash.adjust(-instance.loan.monthly_payment)


@receiver(post_save, sender=Transfer)
def adjust_available_cash_on_transfer_save(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.to_currency == 'CSH':
        AvailableCash.adjust(instance.to_amount)
    elif instance.from_currency == 'CSH':
        AvailableCash.adjust(-instance.from_amount)


@receiver(post_delete, sender=Transfer)
def restore_available_cash_on_transfer_delete(sender, instance, **kwargs):
    if instance.to_currency == 'CSH':
        AvailableCash.adjust(-instance.to_amount)
    elif instance.from_currency == 'CSH':
        AvailableCash.adjust(instance.from_amount)