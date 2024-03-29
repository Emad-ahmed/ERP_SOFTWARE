# Generated by Django 3.2.9 on 2024-01-15 18:16

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ErpApp', '0006_deleveryadd_description'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceproduct',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='setpos',
            name='delivery_status',
            field=models.CharField(blank=True, default='null', max_length=100, null=True),
        ),
    ]