# Generated by Django 3.1 on 2022-01-17 22:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0007_auto_20220117_2246'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transaction',
            name='payment_id',
        ),
    ]
