# Generated by Django 3.0.5 on 2020-05-04 07:40

import archives.helpers.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0028_auto_20200504_1033'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seasonmodel',
            name='last_watched_episode',
            field=models.PositiveSmallIntegerField(blank=True, null=True, validators=[archives.helpers.validators.skip_if_none_none_zero_positive_validator], verbose_name='Last watched episode of a current season'),
        ),
    ]
