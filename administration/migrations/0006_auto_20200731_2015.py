# Generated by Django 3.0.8 on 2020-07-31 17:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0005_auto_20200729_2022'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='entrieschangelog',
            constraint=models.UniqueConstraint(condition=models.Q(operation_type__in=('DELETE', 'CREATE')), fields=('object_id', 'operation_type', 'content_type_id'), name='multiple_delete_or_update_exclusion'),
        ),
    ]
