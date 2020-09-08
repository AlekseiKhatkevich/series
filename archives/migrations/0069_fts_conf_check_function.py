# Generated by Django 3.1.1 on 2020-09-08 07:44

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('archives', '0068_auto_20200907_1714'),
    ]

    operations = [
        migrations.RunSQL(sql=
                          f"""
                            CREATE OR REPLACE FUNCTION fts_conf_check (conf_name varchar) RETURNS BOOLEAN AS
                            $$
                            select conf_name in (SELECT cfgname FROM pg_ts_config);
                            $$
                            LANGUAGE sql;
                            """
                          ,
                          reverse_sql=
                          """
                            drop function if exists fts_conf_check (conf_name varchar);
                            """
                          ),
    ]
