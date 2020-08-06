# Generated by Django 3.1 on 2020-08-06 09:41

from django.db import migrations

from users.models import UserIP


class Migration(migrations.Migration):
    db_table_name = UserIP._meta.db_table

    dependencies = [
        ('users', '0015_deleted_user_slaves_constraint'),
    ]

    operations = [
        migrations.RunSQL(sql=
                          f"""
                            create or replace function count_ips(v_user_id int, v_limit int)
                            returns boolean as $$
                            select count(*) <= v_limit
                            from {db_table_name}
                            where user_id = v_user_id
                            $$ language sql;
                            """
                          ,
                          reverse_sql=
                          """
                            drop function if exists count_ips(v_user_id int, v_limit int);
                            """
                          ), ]