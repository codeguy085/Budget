from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render

from loan.models import Loan, Payment
from .models import Customer


@login_required
def customer_list(request):
    today = date.today()
    first_of_month = today.replace(day=1)

    customers = list(
        Customer.objects.prefetch_related('loans__loan_payments').order_by('-created_at')
    )

    new_pks = set(
        Customer.objects.filter(created_at__date__gte=first_of_month).values_list('pk', flat=True)
    )

    rows = []
    for c in customers:
        loans = list(c.loans.all())
        active_loans = [l for l in loans if not l.is_completed]
        active_count = len(active_loans)
        has_loans = len(loans) > 0

        if active_count == 0:
            status = 'completed' if has_loans else 'none'
        else:
            has_delays = any(
                not p.is_not_delayed
                for l in active_loans
                for p in l.loan_payments.all()
            )
            status = 'delayed' if has_delays else 'active'

        is_new = c.pk in new_pks
        is_fully_paid = active_count == 0 and has_loans

        statuses = []
        if active_count > 0:
            statuses.append('has-active')
        if is_fully_paid:
            statuses.append('fully-paid')
        if is_new:
            statuses.append('new-this-month')

        rows.append({
            'customer': c,
            'active_count': active_count,
            'total_loan': c.total_loan(),
            'total_paid': c.total_paid(),
            'total_remaining': c.total_remaining(),
            'total_revenue': c.total_revenue(),
            'monthly_payment': c.active_montly_payment(),
            'status': status,
            'data_filters': ' '.join(statuses),
        })

    all_count = len(rows)
    has_active_count = sum(1 for r in rows if r['active_count'] > 0)
    fully_paid_count = sum(1 for r in rows if r['status'] == 'completed')
    new_this_month_count = len(new_pks)

    total_payments = Payment.objects.count()
    on_time_payments = Payment.objects.filter(is_not_delayed=True).count()
    collection_rate = round(on_time_payments * 100 / total_payments, 1) if total_payments else 0.0

    new_loans_this_month = Loan.objects.filter(start__date__gte=first_of_month).count()
    total_monthly_payment = Loan.objects.filter(is_completed=False).aggregate(
        s=Coalesce(Sum('monthly_payment'), 0)
    )['s']

    context = {
        'active_nav': 'customers',
        'rows': rows,
        'all_count': all_count,
        'has_active_count': has_active_count,
        'fully_paid_count': fully_paid_count,
        'new_this_month_count': new_this_month_count,
        'collection_rate': collection_rate,
        'new_loans_this_month': new_loans_this_month,
        'total_monthly_payment': total_monthly_payment,
    }
    return render(request, 'customers.html', context)


@login_required
def customer_form(request, pk=None):
    customer = get_object_or_404(Customer, pk=pk) if pk else None
    errors = {}

    if request.method == 'POST':
        data = {
            'name': request.POST.get('name', '').strip(),
            'surname': request.POST.get('surname', '').strip(),
        }
        if not data['name']:
            errors['name'] = 'First name is required.'
        if not data['surname']:
            errors['surname'] = 'Surname is required.'

        if not errors:
            if customer is None:
                customer = Customer.objects.create(
                    name=data['name'],
                    surname=data['surname'],
                )
            else:
                customer.name = data['name']
                customer.surname = data['surname']
                customer.save()
            return redirect('customer_detail', pk=customer.pk)
    elif customer is not None:
        data = {'name': customer.name, 'surname': customer.surname}
    else:
        data = {'name': '', 'surname': ''}

    return render(request, 'create_customer.html', {
        'active_nav': 'customers',
        'data': data,
        'errors': errors,
        'customer': customer,
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(
        Customer.objects.prefetch_related('loans__loan_payments'),
        pk=pk,
    )
    today = date.today()

    loans = list(customer.loans.all())
    active_loans = [l for l in loans if not l.is_completed]
    completed_loans = [l for l in loans if l.is_completed]

    new_loans_this_year = sum(1 for l in loans if l.start.year == today.year)

    has_delays = any(
        not p.is_not_delayed
        for l in active_loans
        for p in l.loan_payments.all()
    )

    total_loaned = customer.total_loan()
    total_paid = customer.total_paid()
    total_remaining = customer.total_remaining()
    total_revenue = customer.total_revenue()
    active_monthly = customer.active_montly_payment()

    total_contractual = sum(l.term * l.monthly_payment for l in loans)
    if total_contractual > 0:
        paid_pct = round(total_paid * 100 / total_contractual, 1)
        remaining_pct = round(100 - paid_pct, 1)
    else:
        paid_pct = 0
        remaining_pct = 0

    total_loans_count = len(loans)
    if total_loans_count > 0:
        active_pct = round(len(active_loans) * 100 / total_loans_count, 1)
        completed_pct = round(100 - active_pct, 1)
    else:
        active_pct = 0
        completed_pct = 0

    loan_rows = []
    for l in sorted(loans, key=lambda x: x.start, reverse=True):
        paid = l.paid_month()
        progress_pct = round(paid * 100 / l.term, 1) if l.term else 0
        loan_rows.append({
            'loan': l,
            'paid_months': paid,
            'remaining_amount': l.remaining_amount(),
            'progress_pct': progress_pct,
        })

    all_payments = []
    for l in loans:
        for p in l.loan_payments.all():
            all_payments.append(p)
    all_payments.sort(key=lambda p: p.paid_at, reverse=True)

    events = []
    for l in loans:
        events.append({
            'type': 'loan_created',
            'date': l.start.date(),
            'loan': l,
        })
        if l.is_completed:
            events.append({
                'type': 'loan_completed',
                'date': l.updated.date(),
                'loan': l,
            })
    for p in all_payments:
        events.append({
            'type': 'payment',
            'date': p.paid_at,
            'payment': p,
        })
    events.sort(key=lambda e: e['date'], reverse=True)

    context = {
        'active_nav': 'customers',
        'customer': customer,
        'all_loans_count': total_loans_count,
        'active_loans_count': len(active_loans),
        'completed_loans_count': len(completed_loans),
        'new_loans_this_year': new_loans_this_year,
        'has_delays': has_delays,
        'has_active_loans': len(active_loans) > 0,
        'total_loaned': total_loaned,
        'total_paid': total_paid,
        'total_remaining': total_remaining,
        'total_revenue': total_revenue,
        'active_monthly': active_monthly,
        'paid_pct': paid_pct,
        'remaining_pct': remaining_pct,
        'active_pct': active_pct,
        'completed_pct': completed_pct,
        'loan_rows': loan_rows,
        'all_payments': all_payments,
        'events': events,
    }
    return render(request, 'customer_detail.html', context)
