# Generated by Django 4.2.7 on 2023-12-13 15:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ErpApp', '0004_setpospurchase'),
    ]

    operations = [
        migrations.AddField(
            model_name='setpospurchase',
            name='description',
            field=models.TextField(blank=True, default='null', null=True),
        ),
    ]