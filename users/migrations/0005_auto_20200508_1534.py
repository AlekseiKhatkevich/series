# Generated by Django 3.0.6 on 2020-05-08 12:34

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20200507_1601'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='master',
            field=models.ForeignKey(blank=True, db_index=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='slaves', to=settings.AUTH_USER_MODEL, verbose_name='Slave account if not null'),
        ),
    ]