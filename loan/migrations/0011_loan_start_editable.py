import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0010_currency_and_transfer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loan',
            name='start',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
