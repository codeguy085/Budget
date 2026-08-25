from datetime import date

from django.db import models
from django.utils import timezone

from user.models import Customer
# Create your models here.

class Loan(models.Model):
    loan_id = models.CharField(unique=True, blank=True, null=True, max_length=20)
    amount = models.IntegerField()
    monthly_payment = models.IntegerField()
    term = models.IntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="loans")
    is_completed = models.BooleanField(default=False)
    start = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f"{self.loan_id} {self.is_completed}"

    def paid_month(self):
        return self.loan_payments.count()

    def remaining_amount(self):
        remaining = (self.term - self.paid_month()) * self.monthly_payment
        return remaining
    
    def revenue(self):
        revenue = self.term * self.monthly_payment - self.amount
        return revenue
    
    def paid_amount(self):
        paid_amount = self.paid_month() * self.monthly_payment
        return paid_amount
    
    def remaining_month(self):
        result = self.term - self.paid_month()
        return result


class Payment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='loan_payments')
    is_not_delayed = models.BooleanField(default=True)
    paid_at = models.DateField(default=date.today)

    def __str__(self):
        return f"{self.loan.loan_id} - {self.paid_at}"


CURRENCY_CHOICES = [
    ('AZN', '₼ AZN'),
    ('USD', '$ USD'),
    ('EUR', '€ EUR'),
]

TRANSFER_CURRENCY_CHOICES = CURRENCY_CHOICES + [
    ('CSH', 'Available Cash (AZN)'),
]

CURRENCY_SYMBOLS = {'AZN': '₼', 'USD': '$', 'EUR': '€', 'CSH': '₼'}
CURRENCY_DISPLAY = {'AZN': 'AZN', 'USD': 'USD', 'EUR': 'EUR', 'CSH': 'Available AZN'}


class AvailableCash(models.Model):
    balance = models.IntegerField(default=0)
    updated = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @classmethod
    def adjust(cls, delta):
        if not delta:
            return
        cls.objects.get_or_create(pk=1)
        cls.objects.filter(pk=1).update(balance=models.F('balance') + delta)

    def __str__(self):
        return f"Available Cash ₼{self.balance}"


class Investment(models.Model):
    amount = models.IntegerField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='AZN')
    added_at = models.DateField(default=date.today)
    note = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at', '-id']

    @property
    def symbol(self):
        return CURRENCY_SYMBOLS.get(self.currency, '')

    def __str__(self):
        return f"Investment {self.symbol}{self.amount} on {self.added_at}"


class Transfer(models.Model):
    from_currency = models.CharField(max_length=3, choices=TRANSFER_CURRENCY_CHOICES)
    to_currency = models.CharField(max_length=3, choices=TRANSFER_CURRENCY_CHOICES)
    from_amount = models.IntegerField()
    to_amount = models.IntegerField()
    rate = models.DecimalField(max_digits=12, decimal_places=4)
    transferred_at = models.DateField(default=date.today)
    note = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transferred_at', '-id']

    @property
    def from_symbol(self):
        return CURRENCY_SYMBOLS.get(self.from_currency, '')

    @property
    def to_symbol(self):
        return CURRENCY_SYMBOLS.get(self.to_currency, '')

    @property
    def from_label(self):
        return CURRENCY_DISPLAY.get(self.from_currency, self.from_currency)

    @property
    def to_label(self):
        return CURRENCY_DISPLAY.get(self.to_currency, self.to_currency)

    def __str__(self):
        return f"Transfer {self.from_symbol}{self.from_amount} {self.from_currency} → {self.to_symbol}{self.to_amount} {self.to_currency}"