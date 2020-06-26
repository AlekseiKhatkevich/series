# Generated by Django 3.0.7 on 2020-06-26 11:48

import datetime
import django.contrib.postgres.fields.ranges
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0041_auto_20200620_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='tvseriesmodel',
            name='translation_years',
            field=django.contrib.postgres.fields.ranges.DateRangeField(default=(datetime.date(2012, 1, 1), datetime.date(2019, 1, 1)), verbose_name='Series years of translation.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='seasonmodel',
            name='series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seasons', to='archives.TvSeriesModel', verbose_name='Parent TV series'),
        ),
    ]