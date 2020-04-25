from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import validators
from django.contrib.postgres import fields as postgres_fields
from django.utils import timezone


from .helpers import file_uploads
from .helpers.validators import skip_if_none_none_zero_positive_validator
from archives import managers


class GroupingModel(models.Model):
    """
    Intermediate model for Many-to-Many recursive relationship between series.
    """
    from_series = models.ForeignKey(
        'TvSeriesModel',
        on_delete=models.CASCADE,
        related_name='group',
    )
    to_series = models.ForeignKey(
        'TvSeriesModel',
        on_delete=models.CASCADE,
        related_name='+',
    )
    reason_for_interrelationship = models.TextField(
        null=True,
        verbose_name='Reason for relationship to an another series.'
    )

    def __str__(self):
        return f'pk - {self.pk} / {self.from_series.name} / pk - {self.from_series_id} <->' \
               f' {self.to_series.name} / pk - {self.to_series_id}'


class TvSeriesModel(models.Model):
    """
    Model represents TV series as a whole.
    """
    objects = managers.TvSeriesManager.from_queryset(managers.TvSeriesQueryset)()

    #  Reverse manager for generic FK relation
    #  https://docs.djangoproject.com/en/3.0/ref/contrib/contenttypes/#reverse-generic-relations
    images = GenericRelation(
        'ImageModel',
        related_query_name='series'
    )

    entry_author = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='series',
        verbose_name='Author of the series entry'
    )
    interrelationship = models.ManyToManyField(
        'self',
        related_name='interrelationship',
        symmetrical=True,
        through=GroupingModel,
        through_fields=('from_series', 'to_series',)
    )
    name = models.CharField(
        max_length=50,
        verbose_name='Name of the series',
        unique=True
    )
    imdb_url = models.URLField(
        verbose_name='IMDB page for the series',
        unique=True,
        db_index=False
    )
    is_finished = models.BooleanField(
        default=False,
        verbose_name='Whether series finished or not'
    )
    rating = models.PositiveSmallIntegerField(
        null=True,
        choices=((number,) * 2 for number in range(1, 11)),
        verbose_name='Rating of TV series from 1 to 10',
        validators=[validators.MinValueValidator(
                limit_value=1,
                message='Zero is not a valid integer for this field', ), ]
    )

    class Meta:
        verbose_name = 'series'
        verbose_name_plural = 'series'
        #default_permissions = []

    def __str__(self):
        return f'{self.pk} / {self.name}'

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

    objects = managers.SeasonManager.from_queryset(managers.SeasonQueryset)()

    non_zero_validator = validators.MinValueValidator(
        limit_value=1,
        message='Zero is not a valid integer for this field',
    )

    series = models.ForeignKey(
        TvSeriesModel,
        on_delete=models.PROTECT,
        related_name='seasons',
        verbose_name='Parent TV series'
    )
    season_number = models.PositiveSmallIntegerField(
        verbose_name='Number of the current season',
        validators=[non_zero_validator, ],
        default=1,
    )
    last_watched_episode = models.PositiveSmallIntegerField(
        null=True,
        verbose_name='Last watched episode of a current season',
        validators=[skip_if_none_none_zero_positive_validator, ],
    )
    number_of_episodes = models.PositiveSmallIntegerField(
        verbose_name='Number of episodes in the current season',
        validators=[non_zero_validator, ],
    )
    episodes = postgres_fields.JSONField(
        null=True,
        verbose_name='Episode number and issue date',
    )

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
        self.full_clean(exclude=('last_watched_episode', 'episodes', ), validate_unique=True)
        super(SeasonModel, self).save(
            force_insert=False, force_update=False, using=None, update_fields=None
        )

    @property
    def is_fully_watched(self) -> bool:
        """
        Is current season are fully watched by user?
        """
        return self.last_watched_episode == self.number_of_episodes

    @property
    def is_finished(self) -> bool or None:
        """
        Whether or not last episode of the season has already been released?
        Returns None if impossible to establish this information from self.episodes.
        """
        last_episode_release_date = self.episodes.get(str(self.number_of_episodes), None)
        if last_episode_release_date is None:
            return None
        now = timezone.now().timestamp()
        return now > last_episode_release_date


class ImageModel(models.Model):
    """
    Model represents an image. Can be attached to any model in the project.
    Based on a Generic FK.
    """

    image = models.ImageField(
        upload_to=file_uploads.save_image_path,
        verbose_name='An image'
    )
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE
    )
    object_id = models.PositiveIntegerField(

    )
    content_object = GenericForeignKey(
        'content_type', 'object_id'
    )

    def __str__(self):
        return f'image - {self.image.name}, model - {self.content_type} - pk={self.object_id}'

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'


