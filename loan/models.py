from django.db import models
from user.models import Customer
# Create your models here.

class Loan(models.Model):
    amount = models.IntegerField()
    monthly_payment = models.IntegerField()
    term = models.IntegerField()
    paid_month = models.IntegerField(default=0)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="loans")
    completed = models.BooleanField(default=False)
    start = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def remaining_amount(self):
        remaining = (self.term - self.paid_month) * self.monthly_payment
        return remaining
    
    def revenue(self):
        revenue = self.term * self.monthly_payment - self.amount
        return revenue
    
    def paid_amount(self):
        paid_amount = self.paid_month * self.monthly_payment
        return paid_amount
    
    def remaining_month(self):
        result = self.term - self.paid_month
        return result