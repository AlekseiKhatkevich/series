# Generated by Django 3.1 on 2020-08-28 10:53

import administration.custom_fields
import administration.helpers.validators
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administration', '0008_auto_20200822_1539'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ipblacklist',
            options={'get_latest_by': ('record_time',), 'verbose_name': 'Ip blacklist.', 'verbose_name_plural': 'Ip blacklists.'},
        ),
        migrations.AlterField(
            model_name='ipblacklist',
            name='ip',
            field=administration.custom_fields.IpAndNetworkField(db_index=True, primary_key=True, serialize=False, unpack_ipv4=True, validators=[administration.helpers.validators.ValidateIpAddressOrNetwork(24)], verbose_name='Ip address.'),
        ),
    ]