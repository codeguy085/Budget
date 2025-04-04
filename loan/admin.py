from django.contrib import admin
from .models import Loan, Payment
# Register your models here.

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["customer", "amount", "term", "monthly_payment", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "is_completed"]
    list_display_links = ["customer", "amount", "term", "monthly_payment", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "is_completed"]

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["loan", "payment", "customer", "paid_at", "is_not_delayed"]
    list_display_links = ["loan", "payment", "customer", "paid_at", "is_not_delayed"]

    @admin.display(description="Payment")
    def payment(self, obj):
        return obj.loan.monthly_payment
    
    @admin.display(description="Customer")
    def customer(self, obj):
        return obj.loan.customer