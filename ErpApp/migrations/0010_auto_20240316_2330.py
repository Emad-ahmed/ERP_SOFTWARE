# Generated by Django 3.2.9 on 2024-03-16 17:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ErpApp', '0009_auto_20240206_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='deleveryadd',
            name='purchase_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ErpApp.setpospurchase'),
        ),
        migrations.AlterField(
            model_name='deleveryadd',
            name='pos_id',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ErpApp.setpos'),
        ),
    ]
