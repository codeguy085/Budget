from django.shortcuts import render
# Create your views here.

def customer_list(request):
    return render(request, "customer_list.html")