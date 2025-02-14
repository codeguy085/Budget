from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Sum, Q


class CustomUser(AbstractUser):
    profile = models.ImageField(upload_to="profile", null=True, blank=True)



class Customer(models.Model):
    name = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f"{self.name} {self.surname}"

    def __str__(self):
        return f"{self.name} {self.surname}"
    
    def active_loans(self):
        return self.loans.filter(completed=False).count()
    
    def all_loans(self):
        return self.loans.count()
    
    def completed_loans(self):
        return self.loans.filter(completed=True).count()

    def total_remaining(self):
        return sum(
            (loan.term - loan.paid_month) * loan.monthly_payment
            for loan in self.loans.filter(completed=False)
        )

    def total_loan(self):
        return self.loans.aggregate(total_amount=models.Sum('amount'))['total_amount'] or 0
    
    def total_paid(self):
        return sum(
            loan.paid_month * loan.monthly_payment
            for loan in self.loans.all()
        )
    
    def total_revenue(self):
        return sum(
            loan.term * loan.monthly_payment - loan.amount
            for loan in self.loans.all()
        )   