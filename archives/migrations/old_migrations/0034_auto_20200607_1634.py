# Generated by Django 3.0.7 on 2020-06-07 13:34

from django.db import migrations, models
import django.db.models.expressions


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0033_auto_20200605_1806'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='groupingmodel',
            options={'verbose_name': 'Group', 'verbose_name_plural': 'Groups'},
        ),
        migrations.AddConstraint(
            model_name='groupingmodel',
            constraint=models.CheckConstraint(check=models.Q(_negated=True, from_series=django.db.models.expressions.F('to_series')), name='interrelationship_on_self'),
        ),
    ]