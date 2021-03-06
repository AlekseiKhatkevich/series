# Generated by Django 3.0.8 on 2020-07-02 18:34

import django.contrib.postgres.fields.hstore
from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations

import archives.helpers.validators


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0047_remove_seasonmodel_episodes'),
    ]

    operations = [
        HStoreExtension(),
        migrations.AddField(
            model_name='seasonmodel',
            name='episodes',
            field=django.contrib.postgres.fields.hstore.HStoreField(blank=True, null=True, validators=[archives.helpers.validators.validate_dict_key_is_digit, archives.helpers.validators.validate_timestamp], verbose_name='Episode number and issue date'),
        ),
    ]
