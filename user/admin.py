from django.contrib import admin
from .models import Customer, CustomUser
# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "username", "email"]
    list_display_links = ["first_name", "last_name", "username", "email"]


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "surname", "active_loans", "completed_loans", "all_loans", "total_remaining", "total_loan", "total_paid", "total_revenue", "created_at"]
    list_display_links = ["name", "surname", "active_loans", "completed_loans", "all_loans", "total_remaining", "total_loan", "total_paid", "total_revenue", "created_at"]
