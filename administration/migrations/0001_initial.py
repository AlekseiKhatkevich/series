# Generated by Django 3.0.8 on 2020-07-26 11:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='EntriesChangeLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('access_time', models.DateTimeField(auto_now_add=True, verbose_name='access_time')),
                ('as_who', models.CharField(choices=[('CREATOR', 'Creator'), ('SLAVE', 'Slave'), ('MASTER', 'Master'), ('FRIEND', 'Friend'), ('ADMIN', 'Admin'), ('LEGACY', 'Legacy')], max_length=7, verbose_name='Status of the accessed user.')),
                ('operation_type', models.CharField(choices=[('CREATE', 'Create'), ('UPDATE', 'Update'), ('DELETE', 'Delete')], max_length=6, verbose_name='Type of the access operation.')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='access_logs', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'Entries log',
                'verbose_name_plural': 'Entries logs',
            },
        ),
    ]