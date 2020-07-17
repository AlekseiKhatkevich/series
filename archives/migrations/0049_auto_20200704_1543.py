# Generated by Django 3.0.8 on 2020-07-04 12:43

import archives.helpers.custom_fields
import archives.helpers.validators
import datetime
import django.contrib.postgres.fields.ranges
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0048_seasonmodel_episodes'),
    ]

    operations = [
        migrations.AddField(
            model_name='seasonmodel',
            name='translation_years',
            field=django.contrib.postgres.fields.ranges.DateRangeField(default=(datetime.date(2018, 1, 1), datetime.date(2019, 1, 1)), validators=[archives.helpers.validators.DateRangeValidator()], verbose_name='Season years of translation.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='seasonmodel',
            name='episodes',
            field=archives.helpers.custom_fields.CustomHStoreField(blank=True, null=True, verbose_name='Episode number and issue date'),
        ),
    ]