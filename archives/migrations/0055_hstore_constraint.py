# Generated by Django 3.0.8 on 2020-07-08 16:24

import django.db.models.expressions
from django.db import migrations, models

import archives.models


class Migration(migrations.Migration):
    db_table_name = archives.models.SeasonModel._meta.db_table
    model_name = archives.models.SeasonModel._meta.model_name
    constraint_name = 'max_key_lte_number_of_episodes'

    dependencies = [
        ('archives', '0054_auto_20200708_1435'),
    ]

    operations = [
        migrations.RunSQL(sql=
                          f"""
                             alter table {db_table_name}
                               drop  CONSTRAINT if exists {constraint_name}
                               ;
                                 alter table {db_table_name}
                                 add CONSTRAINT {constraint_name}
                                   check (
                                      number_of_episodes >= all (akeys(episodes)::int[])
                                   );
                               """
                          ,
                          reverse_sql=
                          f"""
                             alter table {db_table_name}
                               drop CONSTRAINT if exists {constraint_name};
                               """
                          ,
                          state_operations=[
                              migrations.AddConstraint(
                                  model_name=model_name,
                                  constraint=models.CheckConstraint(check=models.Q(
                                      episodes__has_any_keys__gt=django.db.models.expressions.F('number_of_episodes')),
                                                                    name=constraint_name),
                              ), ])]
