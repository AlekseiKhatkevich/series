from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import validators


class TvSeriesModel(models.Model):
    """
    Model represents TV series as a whole.
    """
    #  Reverse manager for generic FK relation
    #  https://docs.djangoproject.com/en/3.0/ref/contrib/contenttypes/#reverse-generic-relations

    images = GenericRelation(
        'ImageModel', related_query_name='series'
    )
    entry_author = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT, related_name='series',
        verbose_name='Author of the series entry'
    )
    #allowed_redactors = models.ManyToManyField(through=)
    name = models.CharField(
        max_length=50, verbose_name='Name of the series', unique=True
    )
    imdb_url = models.URLField(
        verbose_name='IMDB page for the series', unique=True, db_index=False
    )
    is_finished = models.BooleanField(
        default=False, verbose_name='Whether series finished or not'
    )
    rating = models.PositiveSmallIntegerField(
        null=True, choices=((number,) * 2 for number in range(1, 11)),
        verbose_name='Rating of TV series from 1 to 10',
        validators=[validators.MinValueValidator(
                limit_value=1, message='Zero is not a valid integer for this field', ), ]
    )

    class Meta:
        verbose_name = 'series'
        verbose_name_plural = 'series'

    def __str__(self):
        return self.name

    # todo
    @property
    def get_absolute_url(self):
        raise NotImplementedError

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Save method is overridden in order to manually invoke full_clean() method to
        trigger model level validators. I dont know why this doesnt work by default. Need to think about...
        """
        self.full_clean()
        super(TvSeriesModel, self).save(
            force_insert=False, force_update=False, using=None, update_fields=None
        )


class SeasonModel(models.Model):
    """
    Model represents one singular season of a series.
    """

    non_zero_validator = validators.MinValueValidator(
                limit_value=1, message='Zero is not a valid integer for this field',
    )
    series = models.ForeignKey(
        TvSeriesModel, on_delete=models.PROTECT, related_name='seasons', verbose_name='Parent TV series'
    )
    season_number = models.PositiveSmallIntegerField(
        verbose_name='Number of the current season', validators=[non_zero_validator, ], default=1,
    )
    last_watched_episode = models.PositiveSmallIntegerField(
        null=True, verbose_name='Last watched episode of a current season', validators=[non_zero_validator, ]
    )
    #episodes =

    class Meta:
        order_with_respect_to = 'series'
        unique_together = (
             ('series', 'season_number', ),
         )
        index_together = unique_together
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'

    def __str__(self):
        return f'season number - {self.season_number}, series name - {self.series.name}'

    # todo
    @property
    def get_absolute_url(self):
        raise NotImplementedError

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        """
        Save method is overridden in order to manually invoke full_clean() method to
        trigger model level validators. I dont know why this doesnt work by default. Need to think about...
        """
        self.full_clean()
        super(SeasonModel, self).save(
            force_insert=False, force_update=False, using=None, update_fields=None
        )


class ImageModel(models.Model):
    """
    Model represents an image. Can be attached to any model in the project.
    Based on a Generic FK.
    """
    image = models.ImageField(upload_to='uploads/', verbose_name='An image')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'image - {self.image.name}, model - {self.content_type} - pk={self.object_id}'
