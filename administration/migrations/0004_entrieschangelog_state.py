# Generated by Django 3.0.8 on 2020-07-28 14:52

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0003_auto_20200726_1623'),
    ]

    operations = [
        migrations.AddField(
            model_name='entrieschangelog',
            name='state',
            field=django.contrib.postgres.fields.jsonb.JSONField(default={}, verbose_name='Model state before save or delete.'),
            preserve_default=False,
        ),
    ]
