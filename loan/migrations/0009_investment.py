from datetime import date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0008_alter_payment_paid_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='Investment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.IntegerField()),
                ('added_at', models.DateField(default=date.today)),
                ('note', models.CharField(blank=True, default='', max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-added_at', '-id'],
            },
        ),
    ]
