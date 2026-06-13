from django.urls import path

from .views import (
    dashboard,
    loan_list,
    loan_detail,
    loan_form,
    loan_mark_complete,
    payment_list,
    payment_create,
    reports,
    export_loans_csv,
    investment_create,
    cashout_create,
    transfer_create,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("loans/", loan_list, name="loan_list"),
    path("loans/new/", loan_form, name="loan_create"),
    path("loans/<int:pk>/", loan_detail, name="loan_detail"),
    path("loans/<int:pk>/edit/", loan_form, name="loan_edit"),
    path("loans/<int:pk>/complete/", loan_mark_complete, name="loan_mark_complete"),
    path("payments/", payment_list, name="payment_list"),
    path("payments/new/", payment_create, name="payment_create"),
    path("reports/", reports, name="reports"),
    path("reports/export.csv", export_loans_csv, name="export_loans_csv"),
    path("investments/new/", investment_create, name="investment_create"),
    path("investments/cashout/", cashout_create, name="cashout_create"),
    path("transfers/new/", transfer_create, name="transfer_create"),
]
