# Generated by Django 3.0.7 on 2020-06-17 06:24

import archives.helpers.custom_fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0039_auto_20200615_2046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imagemodel',
            name='image_hash',
            field=archives.helpers.custom_fields.ImageHashField(blank=True, max_length=16, null=True, verbose_name='Image hash.'),
        ),
        migrations.AddConstraint(
            model_name='imagemodel',
            constraint=models.CheckConstraint(check=models.Q(image_hash__length=16), name='len_16_constraint'),
        ),
    ]