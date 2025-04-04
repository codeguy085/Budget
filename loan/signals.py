import string
import random
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Loan

def generate_unique_loan_id():
    while True:
        loan_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Loan.objects.filter(loan_id=loan_id).exists():
            return loan_id

@receiver(pre_save, sender=Loan)
def set_unique_loan_id(sender, instance, **kwargs):
    if not instance.loan_id:
        instance.loan_id = generate_unique_loan_id()