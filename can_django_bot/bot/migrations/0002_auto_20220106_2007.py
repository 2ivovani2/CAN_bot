# Generated by Django 3.1 on 2022-01-06 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tguser',
            name='external_id',
            field=models.PositiveBigIntegerField(unique=True, verbose_name='ID телеграмм'),
        ),
    ]