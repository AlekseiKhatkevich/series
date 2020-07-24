# Generated by Django 3.0.8 on 2020-07-23 16:52

from django.contrib.auth import get_user_model
from django.db import migrations, models


class Migration(migrations.Migration):
    db_table_name = get_user_model()._meta.db_table
    constraint_name = 'slaves_of_deleted_user_check'

    dependencies = [
        ('users', '0014_user_deleted_time'),
    ]

    operations = [
        #  Check that our master is not soft-deleted. From slave's side of relations.
        migrations.RunSQL(sql=
                          f"""
                                create or replace function users_user_valid_master(v_master_id integer)
                                returns boolean as $$
                                select deleted = false
                                from {db_table_name}
                                where id = v_master_id
                                $$ language sql;
                            """
                          ,
                          reverse_sql=
                          f"""
                                drop function if exists users_user_valid_master;
                            """
                          ),
        #  Check that if master is soft-deleted then he has not slaves. This is from master's side of
        #  relations.
        migrations.RunSQL(sql=
                          f"""
                                create or replace function users_user_can_delete(v_id integer)
                                returns boolean as $$
                                select count(*) = 0
                                from {db_table_name}
                                where master_id = v_id
                                -- and deleted = false
                                $$ language sql;
                            """
                          ,
                          reverse_sql=
                          f"""
                                drop function if exists users_user_can_delete;
                            """
                          ),
        # Check if our master is not soft-deleted(from slave side of relations) and that if master is soft-
        #  deleted then he doesn't have slaves( from master's side of relations.
        migrations.RunSQL(sql=
                          f"""
                                alter table {db_table_name}
                                add constraint  {constraint_name}
                                check (users_user_valid_master(master_id) and
                                (deleted = false or users_user_can_delete(id)));

                            """
                          ,
                          reverse_sql=
                          f"""
                            alter table {db_table_name}
                            drop CONSTRAINT if exists {constraint_name};
                            """,
                          state_operations=[
                              migrations.AddConstraint(
                                  model_name='user',
                                  constraint=models.CheckConstraint(check=models.Q(
                                      deleted=models.expressions.Func(
                                          models.expressions.F('master_id'),
                                          function='users_user_valid_master')),
                                      name='slaves_of_deleted_user_check'),
                              ), ]), ]
