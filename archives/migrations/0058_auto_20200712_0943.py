# Generated by Django 3.0.8 on 2020-07-12 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0057_add_custom_function'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='seasonmodel',
            constraint=models.CheckConstraint(check=models.Q(episodes__check_episodes=True), name='episodes_sequence_check'),
        ),
    ]
