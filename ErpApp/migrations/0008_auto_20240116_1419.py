# Generated by Django 3.2.9 on 2024-01-16 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ErpApp', '0007_auto_20240116_0016'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceproduct',
            name='po_number',
            field=models.CharField(blank=True, default='so', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='invoiceproduct',
            name='so_number',
            field=models.CharField(blank=True, default='so', max_length=100, null=True),
        ),
    ]