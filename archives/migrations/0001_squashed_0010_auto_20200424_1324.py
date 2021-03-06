# Generated by Django 3.0.5 on 2020-04-24 17:23

import archives.helpers.file_uploads
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    #replaces = [('archives', '0001_initial'), ('archives', '0002_imagemodel'), ('archives', '0003_auto_20200422_1226'), ('archives', '0004_auto_20200422_1555'), ('archives', '0005_auto_20200422_2004'), ('archives', '0006_tvseriesmodel_rating'), ('archives', '0007_auto_20200423_1331'), ('archives', '0008_auto_20200423_2027'), ('archives', '0009_auto_20200423_2042'), ('archives', '0010_auto_20200424_1324')]

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TvSeriesModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Name of the series')),
                ('imdb_url', models.URLField(unique=True, verbose_name='IMDB page for the series')),
                ('entry_author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='series', to=settings.AUTH_USER_MODEL, verbose_name='Author of the series entry')),
                ('is_finished', models.BooleanField(default=False, verbose_name='Whether series finished or not')),
                ('rating', models.PositiveSmallIntegerField(choices=[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9), (10, 10)], null=True, validators=[django.core.validators.MinValueValidator(limit_value=1, message='Zero is not a valid integer for this field')], verbose_name='Rating of TV series from 1 to 10')),
            ],
            options={
                'verbose_name': 'series',
                'verbose_name_plural': 'series',
            },
        ),
        migrations.CreateModel(
            name='ImageModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to=archives.helpers.file_uploads.save_image_path, verbose_name='An image')),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name': 'Image',
                'verbose_name_plural': 'Images',
            },
        ),
        migrations.CreateModel(
            name='GroupingModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason_for_interrelationship', models.TextField(null=True, verbose_name='Reason for relationship to an another series.')),
                ('from_series', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='archives.TvSeriesModel')),
                ('to_series', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='archives.TvSeriesModel')),
            ],
        ),
        migrations.AddField(
            model_name='tvseriesmodel',
            name='interrelationship',
            field=models.ManyToManyField(related_name='_tvseriesmodel_interrelationship_+', through='archives.GroupingModel', to='archives.TvSeriesModel'),
        ),
        migrations.CreateModel(
            name='SeasonModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('series', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='seasons', to='archives.TvSeriesModel', verbose_name='Parent TV series')),
                ('last_watched_episode', models.PositiveSmallIntegerField(null=True, validators=[django.core.validators.MinValueValidator(limit_value=1, message='Zero is not a valid integer for this field')], verbose_name='Last watched episode of a current season')),
                ('season_number', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(limit_value=1, message='Zero is not a valid integer for this field')], verbose_name='Number of the current season')),
                ('number_of_episodes', models.PositiveSmallIntegerField(default=10, validators=[django.core.validators.MinValueValidator(limit_value=1, message='Zero is not a valid integer for this field')], verbose_name='Number of episodes in the current season')),
            ],
            options={
                'verbose_name': 'Season',
                'verbose_name_plural': 'Seasons',
                'unique_together': {('series', 'season_number')},
                'index_together': {('series', 'season_number')},
                'order_with_respect_to': 'series',
            },
        ),
        migrations.AlterField(
            model_name='groupingmodel',
            name='from_series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group', to='archives.TvSeriesModel'),
        ),
    ]
