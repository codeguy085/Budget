from django.contrib import admin
from .models import Investment, Loan, Payment, Transfer
# Register your models here.

class PaymentInline(admin.TabularInline):
    model = Payment
    readonly_fields = ['is_not_delayed', 'paid_at']
    extra = 0


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ["customer", "amount", "loan_id", "term", "monthly_payment", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "is_completed"]
    list_display_links = ["customer", "amount", "loan_id", "term", "monthly_payment", "remaining_month", "paid_amount", "remaining_amount", "revenue", "start", "updated", "is_completed"]
    inlines = [PaymentInline]
    search_fields = ['loan_id']
    autocomplete_fields = ['customer']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["loan", "payment", "customer", "paid_at", "is_not_delayed"]
    list_display_links = ["loan", "payment", "customer", "paid_at", "is_not_delayed"]
    autocomplete_fields = ["loan"]

    @admin.display(description="Payment")
    def payment(self, obj):
        return obj.loan.monthly_payment
    
    @admin.display(description="Customer")
    def customer(self, obj):
        return obj.loan.customer


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ["amount", "currency", "added_at", "note", "created_at"]
    list_filter = ["currency", "added_at"]
    search_fields = ["note"]
    ordering = ["-added_at", "-id"]


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ["from_currency", "from_amount", "to_currency", "to_amount", "rate", "transferred_at", "note"]
    list_filter = ["from_currency", "to_currency", "transferred_at"]
    search_fields = ["note"]
    ordering = ["-transferred_at", "-id"]