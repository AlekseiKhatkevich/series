# Generated by Django 3.1 on 2020-08-28 10:54

from django.db import migrations, models

import administration.models


class Migration(migrations.Migration):
    db_table_name = administration.models.IpBlacklist._meta.db_table
    model_name = administration.models.IpBlacklist._meta.model_name
    constraint_name = 'netmask_check'

    dependencies = [
        ('administration', '0009_auto_20200828_1353'),
    ]

    operations = [
        migrations.RunSQL(sql=
                          f"""
                                alter table {db_table_name}
                                drop  CONSTRAINT if exists {constraint_name}
                                ;
                                alter table {db_table_name} add constraint {constraint_name} check 
                                ((family(ip) = 4 and masklen(ip) between 24 and 32) 
                                or (family(ip) = 6 and masklen(ip) between 120 and 128)); 
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
                                      models.Q(models.Q(('ip__family', 4), ('ip__masklen__in', (24, 32))),
                                               models.Q(('ip__family', 6), ('ip__masklen__in', (120, 128))),
                                               _connector='OR')), name=constraint_name),
                              ),
                             ])]

