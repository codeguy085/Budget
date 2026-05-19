from django.urls import path

from .views import customer_list, customer_detail, customer_form

urlpatterns = [
    path('', customer_list, name='customer_list'),
    path('new/', customer_form, name='customer_create'),
    path('<int:pk>/', customer_detail, name='customer_detail'),
    path('<int:pk>/edit/', customer_form, name='customer_edit'),
]
