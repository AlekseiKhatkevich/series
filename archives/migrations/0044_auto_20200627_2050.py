# Generated by Django 3.0.7 on 2020-06-27 17:50
import datetime

import psycopg2.extras
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0043_auto_20200627_1731'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='tvseriesmodel',
            constraint=models.CheckConstraint(check=models.Q(translation_years__fully_gt=psycopg2.extras.DateRange(None, datetime.date(1896, 1, 6), '()')), name='no_medieval_cinema_check'),
        ),
    ]