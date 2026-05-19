import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("loan", "0007_rename_is_not_deleyad_payment_is_not_delayed"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="paid_at",
            field=models.DateField(default=datetime.date.today),
        ),
    ]
