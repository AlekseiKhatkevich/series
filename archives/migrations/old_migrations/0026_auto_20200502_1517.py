# Generated by Django 3.0.5 on 2020-05-02 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0025_auto_20200502_1452'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='tvseriesmodel',
            constraint=models.CheckConstraint(check=models.Q(imdb_url__icontains='www.imdb.com'), name='url_to_imdb_check'),
        ),
    ]
