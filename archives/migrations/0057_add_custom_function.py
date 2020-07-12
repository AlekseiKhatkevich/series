# Generated by Django 3.0.8 on 2020-07-12 05:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0056_episodes_in_season_constraint'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                """
                create or replace function check_episodes(hstore)
                returns boolean language sql as $$
                select array_agg(key order by key::int) = array_agg(key order by value::date)
                from each($1)
                $$;
                """
            ],
            reverse_sql=[
                """
                DROP FUNCTION  IF EXISTS  check_episodes
                """
            ]
        )
    ]
