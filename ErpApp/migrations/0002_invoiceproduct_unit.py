# Generated by Django 4.2.7 on 2023-11-25 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ErpApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceproduct',
            name='unit',
            field=models.CharField(default='kg', max_length=100),
        ),
    ]