from django.contrib import admin
from .models import Customer, CustomUser
from loan.models import Loan
from django.utils.html import format_html
from django.urls import reverse
# Register your models here.

class LoanInline(admin.TabularInline):
    model = Loan
    readonly_fields = ['loan_link', 'amount', 'monthly_payment', 'term', 'is_completed']
    fields = ['loan_link', 'amount', 'monthly_payment', 'term', 'is_completed']  # Replace loan_id with loan_link
    extra = 0

    def loan_link(self, obj):
        if obj.pk:
            url = reverse('admin:loan_loan_change', args=[obj.pk])
            return format_html('<a href="{}">Loan #{}</a>', url, obj.loan_id)
        return "-"
    loan_link.short_description = "Loan"



@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "username", "email"]
    list_display_links = ["first_name", "last_name", "username", "email"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "surname", "active_montly_payment", "active_loans", "completed_loans", "all_loans", "total_remaining", "total_loan", "total_paid", "total_revenue", "created_at"]
    list_display_links = ["name", "surname", "active_montly_payment", "active_loans", "completed_loans", "all_loans", "total_remaining", "total_loan", "total_paid", "total_revenue", "created_at"]
    inlines = [LoanInline]
    search_fields = ['name', 'surname']