from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('loan', '0010_currency_and_transfer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='investment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='transfer',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
