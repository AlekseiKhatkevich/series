# Generated by Django 3.0.5 on 2020-04-24 13:04

import archives.helpers.validators
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0012_auto_20200424_1447'),
    ]

    operations = [
        migrations.AddField(
            model_name='seasonmodel',
            name='episodes',
            field=django.contrib.postgres.fields.jsonb.JSONField(null=True, verbose_name='Episode number and issue date'),
        ),
        migrations.AlterField(
            model_name='seasonmodel',
            name='last_watched_episode',
            field=models.PositiveSmallIntegerField(null=True, validators=[archives.helpers.validators.skip_if_none_none_zero_positive_validator], verbose_name='Last watched episode of a current season'),
        ),
    ]