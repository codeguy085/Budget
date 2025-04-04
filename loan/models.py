from django.db import models
from user.models import Customer
# Create your models here.

class Loan(models.Model):
    loan_id = models.CharField(unique=True, blank=True, null=True, max_length=20)
    amount = models.IntegerField()
    monthly_payment = models.IntegerField()
    term = models.IntegerField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="loans")
    is_completed = models.BooleanField(default=False)
    start = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.loan_id

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
    paid_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.loan.loan_id} - {self.paid_at}"