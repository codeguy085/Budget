import calendar
import csv
from collections import OrderedDict
from datetime import date, datetime, timedelta

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from user.models import Customer
from .models import Loan, Payment


def _months_in_range(start_date, end_date, max_months=12):
    months = []
    year, month = end_date.year, end_date.month
    start_y, start_m = start_date.year, start_date.month
    for _ in range(max_months):
        months.append((year, month))
        if (year, month) <= (start_y, start_m):
            break
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


def _resolve_period(request, today):
    period = request.GET.get('period', 'this_year')
    custom_start_raw = request.GET.get('start', '')
    custom_end_raw = request.GET.get('end', '')

    if period == 'this_month':
        start_date = today.replace(day=1)
        end_date = today
    elif period == 'last_month':
        first_this = today.replace(day=1)
        last_month_end = first_this - timedelta(days=1)
        start_date = last_month_end.replace(day=1)
        end_date = last_month_end
    elif period == 'all_time':
        start_date = date(2000, 1, 1)
        end_date = today
    elif period == 'custom':
        try:
            start_date = datetime.strptime(custom_start_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            start_date = today.replace(month=1, day=1)
        try:
            end_date = datetime.strptime(custom_end_raw, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            end_date = today
        if start_date > end_date:
            start_date, end_date = end_date, start_date
    else:
        period = 'this_year'
        start_date = today.replace(month=1, day=1)
        end_date = today

    return period, start_date, end_date


def _add_months(d, months):
    month_idx = d.month - 1 + months
    year = d.year + month_idx // 12
    month = month_idx % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@login_required
def loan_detail(request, pk):
    loan = get_object_or_404(
        Loan.objects.select_related('customer').prefetch_related('loan_payments'),
        pk=pk,
    )
    today = date.today()
    start_date = loan.start.date()

    payments = list(loan.loan_payments.order_by('paid_at', 'id'))
    paid_count = len(payments)

    schedule = []
    has_late_or_overdue = False
    for month_num in range(1, loan.term + 1):
        due_date = _add_months(start_date, month_num)
        if month_num <= paid_count:
            payment = payments[month_num - 1]
            if payment.is_not_delayed:
                status = 'on_time'
            else:
                status = 'late'
                has_late_or_overdue = True
            paid_on = payment.paid_at
        else:
            if due_date < today and not loan.is_completed:
                status = 'overdue'
                has_late_or_overdue = True
            else:
                status = 'upcoming'
            paid_on = None
        schedule.append({
            'month': month_num,
            'due_date': due_date,
            'amount': loan.monthly_payment,
            'status': status,
            'paid_on': paid_on,
        })

    if loan.is_completed:
        overall_status = 'completed'
    elif has_late_or_overdue:
        overall_status = 'delayed'
    else:
        overall_status = 'active'

    progress_pct = round(paid_count * 100 / loan.term, 1) if loan.term else 0
    remaining = loan.remaining_amount()
    remaining_months = max(loan.term - paid_count, 0)
    paid_count_after = min(paid_count + 1, loan.term)
    remaining_after = max(remaining - loan.monthly_payment, 0)
    remaining_months_after = max(remaining_months - 1, 0)

    context = {
        'active_nav': 'loans',
        'loan': loan,
        'paid_count': paid_count,
        'remaining': remaining,
        'revenue': loan.revenue(),
        'progress_pct': progress_pct,
        'schedule': schedule,
        'overall_status': overall_status,
        'remaining_months': remaining_months,
        'paid_count_after': paid_count_after,
        'remaining_after': remaining_after,
        'remaining_months_after': remaining_months_after,
        'today_iso': today.isoformat(),
    }
    return render(request, 'loan_detail.html', context)


@login_required
def payment_create(request):
    if request.method == 'POST':
        loan_id = request.POST.get('loan', '')
        try:
            loan = Loan.objects.get(pk=int(loan_id))
        except (Loan.DoesNotExist, ValueError, TypeError):
            return redirect('loan_list')

        paid_at = date.today()
        paid_at_str = request.POST.get('paid_at', '').strip()
        if paid_at_str:
            try:
                paid_at = datetime.strptime(paid_at_str, '%Y-%m-%d').date()
            except ValueError:
                pass

        is_not_delayed = request.POST.get('is_not_delayed') == 'on'

        Payment.objects.create(
            loan=loan,
            paid_at=paid_at,
            is_not_delayed=is_not_delayed,
        )
        return redirect('loan_detail', pk=loan.pk)

    loan_id = request.GET.get('loan', '')
    try:
        loan = Loan.objects.get(pk=int(loan_id))
    except (Loan.DoesNotExist, ValueError, TypeError):
        return redirect('loan_list')

    paid_count = loan.paid_month()
    remaining = loan.remaining_amount()
    remaining_months = max(loan.term - paid_count, 0)
    paid_count_after = min(paid_count + 1, loan.term)
    remaining_after = max(remaining - loan.monthly_payment, 0)
    remaining_months_after = max(remaining_months - 1, 0)

    context = {
        'active_nav': 'payments',
        'loan': loan,
        'paid_count': paid_count,
        'remaining': remaining,
        'remaining_months': remaining_months,
        'paid_count_after': paid_count_after,
        'remaining_after': remaining_after,
        'remaining_months_after': remaining_months_after,
        'today_iso': date.today().isoformat(),
    }
    return render(request, 'create_payment.html', context)


@login_required
@require_POST
def loan_mark_complete(request, pk):
    loan = get_object_or_404(Loan, pk=pk)
    loan.is_completed = True
    loan.save()
    return redirect('loan_detail', pk=pk)


@login_required
def loan_form(request, pk=None):
    loan = get_object_or_404(Loan, pk=pk) if pk else None
    errors = {}

    if request.method == 'POST':
        data = {
            'customer': request.POST.get('customer', '').strip(),
            'amount': request.POST.get('amount', '').strip(),
            'monthly_payment': request.POST.get('monthly_payment', '').strip(),
            'term': request.POST.get('term', '').strip(),
        }

        customer = None
        if not data['customer']:
            errors['customer'] = 'Please select a customer.'
        else:
            try:
                customer = Customer.objects.get(pk=int(data['customer']))
            except (Customer.DoesNotExist, ValueError):
                errors['customer'] = 'Customer not found.'

        amount_int = None
        try:
            amount_int = int(data['amount'])
            if amount_int <= 0:
                errors['amount'] = 'Amount must be greater than zero.'
        except (ValueError, TypeError):
            errors['amount'] = 'Enter a valid amount.'

        monthly_int = None
        try:
            monthly_int = int(data['monthly_payment'])
            if monthly_int <= 0:
                errors['monthly_payment'] = 'Monthly payment must be greater than zero.'
        except (ValueError, TypeError):
            errors['monthly_payment'] = 'Enter a valid monthly payment.'

        term_int = None
        try:
            term_int = int(data['term'])
            if term_int <= 0:
                errors['term'] = 'Term must be greater than zero.'
        except (ValueError, TypeError):
            errors['term'] = 'Enter a valid term.'

        if loan is not None and term_int is not None:
            paid = loan.paid_month()
            if term_int < paid:
                errors['term'] = f'Term cannot be less than already paid months ({paid}).'

        if not errors:
            if loan is None:
                loan = Loan.objects.create(
                    customer=customer,
                    amount=amount_int,
                    monthly_payment=monthly_int,
                    term=term_int,
                )
            else:
                loan.customer = customer
                loan.amount = amount_int
                loan.monthly_payment = monthly_int
                loan.term = term_int
                loan.save()
            return redirect('loan_detail', pk=loan.pk)
    elif loan is not None:
        data = {
            'customer': str(loan.customer_id),
            'amount': str(loan.amount),
            'monthly_payment': str(loan.monthly_payment),
            'term': str(loan.term),
        }
    else:
        data = {
            'customer': request.GET.get('customer', ''),
            'amount': '',
            'monthly_payment': '',
            'term': '',
        }

    customers = Customer.objects.order_by('name', 'surname')
    context = {
        'active_nav': 'loans',
        'customers': customers,
        'data': data,
        'errors': errors,
        'loan': loan,
    }
    return render(request, 'create_loan.html', context)


@login_required
def loan_list(request):
    today = date.today()
    loans = list(
        Loan.objects
        .select_related('customer')
        .prefetch_related('loan_payments')
        .order_by('-start')
    )

    rows = []
    active_remaining_total = 0
    yield_ratios = []

    for l in loans:
        if l.is_completed:
            status = 'completed'
        else:
            has_delays = any(not p.is_not_delayed for p in l.loan_payments.all())
            status = 'delayed' if has_delays else 'active'

        paid = l.paid_month()
        remaining = l.remaining_amount()
        revenue = l.revenue()
        progress_pct = round(paid * 100 / l.term, 1) if l.term else 0

        paid_this_month = any(
            p.paid_at.year == today.year and p.paid_at.month == today.month
            for p in l.loan_payments.all()
        )

        if l.is_completed or paid >= l.term:
            next_due_date = None
            days_until_next = None
            days_sort_key = 999999
        else:
            next_due_date = _add_months(l.start.date(), paid + 1)
            days_until_next = (next_due_date - today).days
            days_sort_key = days_until_next

        if not l.is_completed:
            active_remaining_total += remaining

        if l.amount > 0:
            yield_ratios.append(revenue / l.amount)

        rows.append({
            'loan': l,
            'status': status,
            'paid_months': paid,
            'remaining': remaining,
            'revenue': revenue,
            'progress_pct': progress_pct,
            'paid_this_month': paid_this_month,
            'next_due_date': next_due_date,
            'days_until_next': days_until_next,
            'days_sort_key': days_sort_key,
        })

    avg_yield = round(sum(yield_ratios) * 100 / len(yield_ratios), 1) if yield_ratios else 0

    customers = Customer.objects.order_by('name', 'surname')
    years = sorted({l.start.year for l in loans}, reverse=True)

    context = {
        'active_nav': 'loans',
        'rows': rows,
        'total_count': len(rows),
        'active_count': sum(1 for r in rows if r['status'] == 'active'),
        'completed_count': sum(1 for r in rows if r['status'] == 'completed'),
        'delayed_count': sum(1 for r in rows if r['status'] == 'delayed'),
        'active_remaining_total': active_remaining_total,
        'avg_yield': avg_yield,
        'customers': customers,
        'years': years,
    }
    return render(request, 'loans.html', context)


@login_required
def reports(request):
    today = date.today()
    period, start_date, end_date = _resolve_period(request, today)

    loans_in_range = list(
        Loan.objects
        .select_related('customer')
        .prefetch_related('loan_payments')
        .filter(start__date__gte=start_date, start__date__lte=end_date)
    )
    payments_in_range = list(
        Payment.objects
        .select_related('loan', 'loan__customer')
        .filter(paid_at__gte=start_date, paid_at__lte=end_date)
    )

    chart_months = _months_in_range(start_date, end_date, max_months=12)
    chart_months_set = set(chart_months)

    revenue_by_month = OrderedDict((m, 0) for m in chart_months)
    for l in loans_in_range:
        key = (l.start.year, l.start.month)
        if key in chart_months_set:
            revenue_by_month[key] += l.revenue()

    peak_month_index = None
    if revenue_by_month:
        max_rev = max(revenue_by_month.values())
        if max_rev > 0:
            for i, (m, v) in enumerate(revenue_by_month.items()):
                if v == max_rev:
                    peak_month_index = i
                    break

    status_chart_months = chart_months[-6:] if len(chart_months) >= 6 else chart_months
    status_months_set = set(status_chart_months)
    status_data = OrderedDict((m, {'on_time': 0, 'late': 0, 'total_amount': 0}) for m in status_chart_months)
    for p in payments_in_range:
        key = (p.paid_at.year, p.paid_at.month)
        if key in status_months_set:
            if p.is_not_delayed:
                status_data[key]['on_time'] += 1
            else:
                status_data[key]['late'] += 1
            status_data[key]['total_amount'] += p.loan.monthly_payment

    status_rows = []
    for (y, m), counts in status_data.items():
        total = counts['on_time'] + counts['late']
        if total:
            on_time_pct = round(counts['on_time'] * 100 / total, 1)
            late_pct = round(100 - on_time_pct, 1)
        else:
            on_time_pct = 0
            late_pct = 0
        status_rows.append({
            'label': date(y, m, 1).strftime('%B %Y').upper(),
            'total_amount': counts['total_amount'],
            'on_time_pct': on_time_pct,
            'late_pct': late_pct,
            'has_data': total > 0,
        })

    heatmap_end = end_date
    heatmap_start = max(end_date - timedelta(days=27), start_date)
    heatmap_days = []
    cursor = heatmap_start
    while cursor <= heatmap_end:
        heatmap_days.append(cursor)
        cursor += timedelta(days=1)
    heatmap_days = heatmap_days[-28:]

    payments_by_day = {}
    for p in payments_in_range:
        if heatmap_days and heatmap_days[0] <= p.paid_at <= heatmap_days[-1]:
            payments_by_day[p.paid_at] = payments_by_day.get(p.paid_at, 0) + 1

    max_per_day = max(payments_by_day.values(), default=0)
    heatmap_cells = []
    for d in heatmap_days:
        count = payments_by_day.get(d, 0)
        if max_per_day == 0 or count == 0:
            intensity = 0
        else:
            ratio = count / max_per_day
            if ratio < 0.33:
                intensity = 1
            elif ratio < 0.66:
                intensity = 2
            else:
                intensity = 3
        heatmap_cells.append({'date': d, 'count': count, 'intensity': intensity})

    top_loans_list = []
    for l in loans_in_range:
        revenue = l.revenue()
        if l.is_completed:
            status = 'completed'
        else:
            has_delays = any(not p.is_not_delayed for p in l.loan_payments.all())
            status = 'delayed' if has_delays else 'active'
        top_loans_list.append({'loan': l, 'revenue': revenue, 'status': status})
    top_loans_list.sort(key=lambda x: x['revenue'], reverse=True)
    top_loans_list = top_loans_list[:10]

    watchlist_map = {}
    for p in Payment.objects.filter(is_not_delayed=False, loan__is_completed=False).select_related('loan__customer'):
        c = p.loan.customer
        if c.id not in watchlist_map:
            watchlist_map[c.id] = {'customer': c, 'late_count': 0, 'at_risk': 0}
        watchlist_map[c.id]['late_count'] += 1
        watchlist_map[c.id]['at_risk'] += p.loan.monthly_payment
    watchlist = []
    for entry in watchlist_map.values():
        late_count = entry['late_count']
        if late_count >= 4:
            entry['severity'] = 'critical'
        elif late_count >= 2:
            entry['severity'] = 'overdue'
        else:
            entry['severity'] = 'pending'
        watchlist.append(entry)
    watchlist.sort(key=lambda e: (e['late_count'], e['at_risk']), reverse=True)
    watchlist = watchlist[:8]

    loan_count = len(loans_in_range)
    avg_loan_size = round(sum(l.amount for l in loans_in_range) / loan_count) if loan_count else 0
    avg_term = round(sum(l.term for l in loans_in_range) / loan_count, 1) if loan_count else 0

    total_payments_in_range = len(payments_in_range)
    on_time_payments_in_range = sum(1 for p in payments_in_range if p.is_not_delayed)
    on_time_rate = round(on_time_payments_in_range * 100 / total_payments_in_range, 1) if total_payments_in_range else 0
    late_count_in_range = total_payments_in_range - on_time_payments_in_range
    late_ratio = late_count_in_range / total_payments_in_range if total_payments_in_range else 0
    if total_payments_in_range == 0:
        risk_level = 'No Data'
        risk_class = 'on-surface-variant'
        risk_blurb = 'No payments in this period.'
    elif late_ratio < 0.05:
        risk_level = 'Low'
        risk_class = 'secondary'
        risk_blurb = f'{late_count_in_range} late of {total_payments_in_range} payments.'
    elif late_ratio < 0.15:
        risk_level = 'Medium'
        risk_class = 'tertiary'
        risk_blurb = f'{late_count_in_range} late of {total_payments_in_range} payments.'
    else:
        risk_level = 'High'
        risk_class = 'error'
        risk_blurb = f'{late_count_in_range} late of {total_payments_in_range} payments.'

    revenue_chart_data = {
        'labels': [date(y, m, 1).strftime('%b %y') for (y, m) in chart_months],
        'data': [int(round(revenue_by_month[m])) for m in chart_months],
        'peakIndex': peak_month_index,
    }

    new_loans_by_month = OrderedDict((m, 0) for m in chart_months)
    collected_by_month = OrderedDict((m, 0) for m in chart_months)
    for l in loans_in_range:
        key = (l.start.year, l.start.month)
        if key in chart_months_set:
            new_loans_by_month[key] += l.amount
    for p in payments_in_range:
        key = (p.paid_at.year, p.paid_at.month)
        if key in chart_months_set:
            collected_by_month[key] += p.loan.monthly_payment
    gap_by_month = {m: new_loans_by_month[m] - collected_by_month[m] for m in chart_months}

    total_deployed = sum(new_loans_by_month.values())
    total_collected = sum(collected_by_month.values())
    net_invested = total_deployed - total_collected

    capital_flow_data = {
        'labels': [date(y, m, 1).strftime('%b %y') for (y, m) in chart_months],
        'new_loans': [new_loans_by_month[m] for m in chart_months],
        'collected': [collected_by_month[m] for m in chart_months],
        'gap': [gap_by_month[m] for m in chart_months],
    }

    context = {
        'active_nav': 'reports',
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'custom_start_iso': start_date.isoformat(),
        'custom_end_iso': end_date.isoformat(),
        'revenue_chart_data': revenue_chart_data,
        'capital_flow_data': capital_flow_data,
        'total_deployed': total_deployed,
        'total_collected': total_collected,
        'net_invested': net_invested,
        'status_rows': status_rows,
        'heatmap_cells': heatmap_cells,
        'top_loans': top_loans_list,
        'watchlist': watchlist,
        'avg_loan_size': avg_loan_size,
        'avg_term': avg_term,
        'on_time_rate': on_time_rate,
        'risk_level': risk_level,
        'risk_class': risk_class,
        'risk_blurb': risk_blurb,
    }
    return render(request, 'reports.html', context)


@login_required
def export_loans_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="loans.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Loan ID', 'Customer', 'Amount', 'Monthly Payment', 'Term (months)',
        'Paid Months', 'Remaining', 'Revenue', 'Status', 'Start Date',
    ])
    for loan in Loan.objects.select_related('customer').prefetch_related('loan_payments').order_by('-start'):
        paid = loan.loan_payments.count()
        if loan.is_completed:
            status = 'Completed'
        else:
            has_delays = any(not p.is_not_delayed for p in loan.loan_payments.all())
            status = 'Delayed' if has_delays else 'Active'
        writer.writerow([
            loan.loan_id,
            loan.customer.get_full_name(),
            loan.amount,
            loan.monthly_payment,
            loan.term,
            paid,
            loan.remaining_amount(),
            loan.revenue(),
            status,
            loan.start.date().isoformat(),
        ])
    return response


@login_required
def payment_list(request):
    payments = list(
        Payment.objects
        .select_related('loan', 'loan__customer')
        .order_by('-paid_at', '-id')
    )

    rows = []
    on_time_count = 0
    late_count = 0
    for p in payments:
        if p.is_not_delayed:
            filter_status = 'on-time'
            on_time_count += 1
        else:
            filter_status = 'late'
            late_count += 1
        rows.append({
            'payment': p,
            'filter_status': filter_status,
        })

    context = {
        'active_nav': 'payments',
        'rows': rows,
        'total_count': len(rows),
        'on_time_count': on_time_count,
        'late_count': late_count,
        'customers': Customer.objects.order_by('name', 'surname'),
    }
    return render(request, 'payments.html', context)


def _last_12_months(today):
    months = []
    year, month = today.year, today.month
    for _ in range(12):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return list(reversed(months))


@login_required
def dashboard(request):
    today = date.today()
    first_of_month = today.replace(day=1)

    loans = list(Loan.objects.select_related('customer').prefetch_related('loan_payments'))
    active_loans = [l for l in loans if not l.is_completed]
    completed_loans = [l for l in loans if l.is_completed]

    remaining_balance = sum(l.remaining_amount() for l in active_loans)

    total_profit = sum(l.revenue() for l in loans)
    year_profit = sum(l.revenue() for l in loans if l.start.year == today.year)

    active_count = len(active_loans)
    completed_count = len(completed_loans)
    current_month_monthly = sum(l.monthly_payment for l in active_loans)
    total_loans = len(loans)
    total_borrowers = Customer.objects.count()
    new_borrowers_this_month = Customer.objects.filter(created_at__gte=first_of_month).count()

    delayed_loan_ids = set(
        Payment.objects.filter(
            is_not_delayed=False,
            loan__is_completed=False,
        ).values_list('loan_id', flat=True)
    )
    delayed_count = len(delayed_loan_ids)
    on_time_count = max(active_count - delayed_count, 0)

    circumference = 251.2
    if total_loans > 0:
        on_time_dash = round(circumference * on_time_count / total_loans, 2)
        delayed_dash = round(circumference * delayed_count / total_loans, 2)
        completed_dash = round(circumference * completed_count / total_loans, 2)
    else:
        on_time_dash = delayed_dash = completed_dash = 0
    on_time_plus_delayed_dash = round(on_time_dash + delayed_dash, 2)

    top_customers_raw = []
    for customer in Customer.objects.all():
        remaining = customer.total_remaining()
        if remaining > 0:
            top_customers_raw.append((customer, remaining))
    top_customers_raw.sort(key=lambda x: x[1], reverse=True)
    top_customers_raw = top_customers_raw[:5]

    top_max = top_customers_raw[0][1] if top_customers_raw else 0
    top_customers = [
        {
            'customer': c,
            'remaining': r,
            'pct': round(r * 100 / top_max, 1) if top_max else 0,
        }
        for c, r in top_customers_raw
    ]

    recent_payments = (
        Payment.objects
        .select_related('loan', 'loan__customer')
        .order_by('-paid_at', '-id')[:5]
    )

    months = _last_12_months(today)
    paid_by_month = OrderedDict((m, 0) for m in months)
    expected_by_month = OrderedDict((m, 0) for m in months)
    months_set = set(months)

    for p in Payment.objects.select_related('loan').filter(
        paid_at__gte=date(months[0][0], months[0][1], 1)
    ):
        key = (p.paid_at.year, p.paid_at.month)
        if key in paid_by_month:
            paid_by_month[key] += p.loan.monthly_payment

    for l in loans:
        y, m = l.start.year, l.start.month
        for i in range(l.term):
            mm = m + i
            yy = y + (mm - 1) // 12
            mm = ((mm - 1) % 12) + 1
            key = (yy, mm)
            if key in months_set:
                expected_by_month[key] += l.monthly_payment

    month_labels = [date(y, m, 1).strftime('%b %y') for (y, m) in months]
    cash_flow_data = {
        'labels': month_labels,
        'paid': list(paid_by_month.values()),
        'expected': list(expected_by_month.values()),
    }

    context = {
        'active_nav': 'dashboard',
        'current_year': today.year,
        'remaining_balance': remaining_balance,
        'total_profit': total_profit,
        'year_profit': year_profit,
        'active_count': active_count,
        'completed_count': completed_count,
        'current_month_monthly': current_month_monthly,
        'total_loans': total_loans,
        'total_borrowers': total_borrowers,
        'new_borrowers_this_month': new_borrowers_this_month,
        'on_time_count': on_time_count,
        'delayed_count': delayed_count,
        'on_time_dash': on_time_dash,
        'delayed_dash': delayed_dash,
        'completed_dash': completed_dash,
        'on_time_plus_delayed_dash': on_time_plus_delayed_dash,
        'top_customers': top_customers,
        'recent_payments': recent_payments,
        'cash_flow_data': cash_flow_data,
    }
    return render(request, 'dashboard.html', context)
