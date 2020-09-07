# Generated by Django 3.1.1 on 2020-09-05 11:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0066_auto_20200904_1426'),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
               """
                create extension IF NOT EXISTS  hunspell_en_us
                    schema pg_catalog
                    version '1.0';
                
                comment on extension hunspell_en_us is 'en_US Hunspell Dictionary';
                
                create extension IF NOT EXISTS hunspell_ru_ru
                    schema pg_catalog
                    version '1.0';
                
                comment on extension hunspell_ru_ru is 'Russian Hunspell Dictionary';
                
                create extension IF NOT EXISTS hunspell_ru_ru_aot
                    schema pg_catalog
                    version '1.0';
                
                comment on extension hunspell_ru_ru_aot is 'Russian Hunspell Dictionary (from AOT.ru group)';
                
                create extension hunspell_fr
                    schema public
                    version '1.0';

                comment on extension hunspell_fr is 'French Hunspell Dictionary';
               """
            ],
            reverse_sql=[
                """
                DROP EXTENSION IF EXISTS
                    hunspell_en_us,
                    hunspell_ru_ru,
                    hunspell_ru_ru_aot,
                    hunspell_fr
                CASCADE 
                """
            ]
        )
    ]
