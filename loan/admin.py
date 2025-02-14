from django.contrib import admin
from .models import Loan
# Register your models here.

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["customer", "amount", "term", "monthly_payment", "paid_month", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "completed"]
    list_display_links = ["customer", "amount", "term", "monthly_payment", "paid_month", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "completed"]
