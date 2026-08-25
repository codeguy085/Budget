from django.db import migrations
from django.db.models import Sum


def seed_available_cash(apps, schema_editor):
    Loan = apps.get_model('loan', 'Loan')
    Payment = apps.get_model('loan', 'Payment')
    AvailableCash = apps.get_model('loan', 'AvailableCash')

    deployed = Loan.objects.aggregate(s=Sum('amount'))['s'] or 0
    collected = Payment.objects.aggregate(s=Sum('loan__monthly_payment'))['s'] or 0

    AvailableCash.objects.update_or_create(
        pk=1,
        defaults={'balance': collected - deployed},
    )


def unseed_available_cash(apps, schema_editor):
    AvailableCash = apps.get_model('loan', 'AvailableCash')
    AvailableCash.objects.filter(pk=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("loan", "0014_availablecash_alter_transfer_from_currency_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_available_cash, unseed_available_cash),
    ]
