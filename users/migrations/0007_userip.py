# Generated by Django 3.0.6 on 2020-05-16 14:53

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20200513_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserIP',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.GenericIPAddressField(blank=True, null=True, verbose_name='User ip address')),
                ('sample_time', models.DateTimeField(auto_now=True, verbose_name='User ip sample time')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_ip', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User ip address.',
                'verbose_name_plural': 'Users ip addresses.',
            },
        ),
    ]