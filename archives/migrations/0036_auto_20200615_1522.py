# Generated by Django 3.0.7 on 2020-06-15 12:22

import archives.helpers.file_uploads
import archives.helpers.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('archives', '0035_auto_20200607_2027'),
    ]

    operations = [
        migrations.AddField(
            model_name='imagemodel',
            name='image_hash',
            field=models.CharField(default=django.utils.timezone.now, max_length=50, verbose_name='Image hash.'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='groupingmodel',
            name='from_series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group', to='archives.TvSeriesModel', verbose_name='relationship with series.'),
        ),
        migrations.AlterField(
            model_name='groupingmodel',
            name='to_series',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='group_to', to='archives.TvSeriesModel', verbose_name='relationship with series.'),
        ),
        migrations.AlterField(
            model_name='imagemodel',
            name='image',
            field=models.ImageField(upload_to=archives.helpers.file_uploads.save_image_path, validators=[archives.helpers.validators.IsImageValidator()], verbose_name='An image'),
        ),
    ]
