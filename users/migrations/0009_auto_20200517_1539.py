# Generated by Django 3.0.6 on 2020-05-17 12:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20200516_2207'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='userip',
            options={'verbose_name': 'User ip address.', 'verbose_name_plural': 'User ip addresses.'},
        ),
        migrations.AlterField(
            model_name='userip',
            name='ip',
            field=models.GenericIPAddressField(default='127.0.0.7', verbose_name='User ip address'),
            preserve_default=False,
        ),
    ]
