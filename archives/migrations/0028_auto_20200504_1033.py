# Generated by Django 3.0.5 on 2020-05-04 07:33

import archives.helpers.custom_fields
import archives.helpers.validators
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0027_auto_20200503_0940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seasonmodel',
            name='last_watched_episode',
            field=archives.helpers.custom_fields.CustomPositiveSmallIntegerField(blank=True, null=True, validators=[archives.helpers.validators.skip_if_none_none_zero_positive_validator], verbose_name='Last watched episode of a current season'),
        ),
    ]
