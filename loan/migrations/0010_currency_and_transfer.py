from datetime import date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0009_investment'),
    ]

    operations = [
        migrations.AddField(
            model_name='investment',
            name='currency',
            field=models.CharField(
                choices=[('AZN', '₼ AZN'), ('USD', '$ USD'), ('EUR', '€ EUR')],
                default='AZN',
                max_length=3,
            ),
        ),
        migrations.CreateModel(
            name='Transfer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('from_currency', models.CharField(
                    choices=[('AZN', '₼ AZN'), ('USD', '$ USD'), ('EUR', '€ EUR')],
                    max_length=3,
                )),
                ('to_currency', models.CharField(
                    choices=[('AZN', '₼ AZN'), ('USD', '$ USD'), ('EUR', '€ EUR')],
                    max_length=3,
                )),
                ('from_amount', models.IntegerField()),
                ('to_amount', models.IntegerField()),
                ('rate', models.DecimalField(decimal_places=4, max_digits=12)),
                ('transferred_at', models.DateField(default=date.today)),
                ('note', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-transferred_at', '-id'],
            },
        ),
    ]
