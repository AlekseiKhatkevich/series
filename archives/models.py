import heapq
import os
from types import MappingProxyType
from typing import KeysView

from BTrees.IOBTree import IOBTree
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres import fields as psgr_fields
from django.core import exceptions, validators
from django.db import models
from django.db.models.functions import Length
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property
from psycopg2.extras import DateRange
from rest_framework.reverse import reverse

import archives.managers
from archives.helpers import custom_fields, custom_functions, file_uploads, validators as custom_validators
from series import constants, error_codes

models.CharField.register_lookup(Length)


class GroupingModel(models.Model):
    """
    Intermediate model for Many-to-Many recursive relationship between series.
    """
    objects = archives.managers.GroupingManager.from_queryset(archives.managers.GroupingQueryset)()

    from_series = models.ForeignKey(
        'TvSeriesModel',
        on_delete=models.CASCADE,
        related_name='group',
        verbose_name='relationship with series.'
    )
    to_series = models.ForeignKey(
        'TvSeriesModel',
        on_delete=models.CASCADE,
        related_name='group_to',
        verbose_name='relationship with series.'
    )
    reason_for_interrelationship = models.TextField(
        verbose_name='Reason for relationship to an another series.',
    )

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        unique_together = (
            ('from_series', 'to_series',),
        )
        constraints = [
            models.CheckConstraint(
                name='interrelationship_on_self',
                check=~models.Q(from_series=models.F('to_series')),
            )]

    def __str__(self):
        return f'pk - {self.pk} / {self.from_series.name} / pk - {self.from_series_id} <->' \
               f' {self.to_series.name} / pk - {self.to_series_id}'

    def clean(self):
        if self.from_series == self.to_series:
            raise exceptions.ValidationError(
                *error_codes.INTERRELATIONSHIP_ON_SELF
            )

    def save(self, fc=True, *args, **kwargs):
        if fc:
            self.full_clean(validate_unique=True)
        super().save(*args, **kwargs)

    def __hash__(self):
        """
        Make unique hash by combining 3 fields 'from_series_id', 'to_series_id' and 'reason_for_interrelationship'.
        """
        # return hash(f'{self.from_series_id}{self.from_series_id}{self.reason_for_interrelationship}')
        return hash((self.from_series_id, self.from_series_id, self.reason_for_interrelationship))

    def __eq__(self, other):
        """
        Compare hashes im at least one of objects does not have pk yet.
        """
        if None in (self.pk, other.pk,):
            return self.__hash__() == other.__hash__()
        else:
            return super().__eq__(other)


class TvSeriesModel(models.Model):
    """
    Model represents TV series as a whole.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_model_state = model_to_dict(self, exclude='interrelationship')

    objects = archives.managers.TvSeriesManager.from_queryset(archives.managers.TvSeriesQueryset)()

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
        db_index=False,
        validators=[
            custom_validators.ValidateUrlDomain('www.imdb.com'),
            custom_validators.ValidateIfUrlIsAlive(3, ),
        ])
    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        choices=([(number,) * 2 for number in range(1, 11)] + [(None, 'No rating given'), ]),
        verbose_name='Rating of TV series from 1 to 10',
        validators=[
            validators.MinValueValidator(
                limit_value=1,
                message=error_codes.ZERO_IS_NOT_VALID, ),
            validators.MaxValueValidator(
                limit_value=10,
                message='Maximal value for this field is 10'
            )])
    translation_years = psgr_fields.DateRangeField(
        verbose_name='Series years of translation.',
        validators=[custom_validators.DateRangeValidator(upper_inf_allowed=True)]
    )

    class Meta:
        verbose_name = 'series'
        verbose_name_plural = 'series'
        permissions = (
            ('permissiveness', 'Allow any action',),
        )
        constraints = [
            models.CheckConstraint(
                name='rating_from_1_to_10',
                check=models.Q(rating__range=(1, 10)) | models.Q(rating__isnull=True),
            ),
            models.CheckConstraint(
                name='url_to_imdb_check',
                check=models.Q(imdb_url__icontains='www.imdb.com')
            ),
            models.CheckConstraint(
                name='no_medieval_cinema_check',
                check=models.Q(
                    translation_years__fully_gt=DateRange(None, constants.LUMIERE_FIRST_FILM_DATE, '()')
                )),
            #  This constraint is a fake constraint used in state_operations in migration
            #  0045_defend_future_constraint
            models.CheckConstraint(
                name='defend_future_check',
                check=~models.Q(translation_years__contained_by=
                                DateRange(timezone.datetime(2030, 1, 1).date(), None, '()')
                                ))]

    def __str__(self):
        return f'{self.pk} / {self.name}'

    def save(self, fc=True, *args, **kwargs):
        # Exclude 'url_to_imdb' from field validation if field hasn't changed or
        # model instance is not just created.
        if fc:
            exclude = \
                ('imdb_url',) if self.pk is not None and ('url_to_imdb' not in self.changed_fields) \
                    else ()
            self.full_clean(exclude=exclude, validate_unique=True)

        super().save(*args, **kwargs)
        self._original_model_state = model_to_dict(self, exclude='interrelationship')

    @cached_property
    def get_absolute_url(self):
        return reverse('tvseries-detail', args=(self.pk,))

    @property
    def changed_fields(self) -> KeysView:
        """
        Returns a set(dict keys view) of changed fields in model.
        """
        current_model_state = model_to_dict(self, exclude='interrelationship')
        changed_fields = dict(current_model_state.items() - self._original_model_state.items()).keys()
        return changed_fields

    @property
    def is_finished(self) -> bool:
        """
        Returns whether current series is finished or not.
        """
        now = timezone.now().date
        infinity = timezone.datetime.max.date()

        if now < (self.translation_years.upper or infinity):
            return False
        else:
            return True


class SeasonModel(models.Model):
    """
    Model represents one singular season of a series.
    """

    objects = archives.managers.SeasonManager.from_queryset(archives.managers.SeasonQueryset)()

    non_zero_validator = validators.MinValueValidator(
        limit_value=1,
        message=error_codes.ZERO_IS_NOT_VALID,
    )

    series = models.ForeignKey(
        TvSeriesModel,
        on_delete=models.CASCADE,
        related_name='seasons',
        verbose_name='Parent TV series'
    )
    season_number = models.PositiveSmallIntegerField(
        verbose_name='Number of the current season',
        validators=[non_zero_validator, ],
        default=1,
    )
    last_watched_episode = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Last watched episode of a current season',
        validators=[custom_validators.skip_if_none_none_zero_positive_validator, ],
    )
    number_of_episodes = models.PositiveSmallIntegerField(
        verbose_name='Number of episodes in the current season',
        validators=[non_zero_validator, ],
    )
    episodes = psgr_fields.JSONField(
        null=True,
        blank=True,
        verbose_name='Episode number and issue date',
        validators=[
            custom_validators.validate_dict_key_is_digit,
            custom_validators.validate_timestamp,
        ], )

    class Meta:
        order_with_respect_to = 'series'
        unique_together = (
            ('series', 'season_number',),
        )
        index_together = unique_together
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'
        constraints = [
            # (Last_watched_episodes >= 1 or None)  and  number_of_episodes >= 1.
            models.CheckConstraint(
                name='last_watched_episode_and_number_of_episodes_are_gte_one',
                check=(models.Q(last_watched_episode__gte=1) | models.Q(last_watched_episode__isnull=True))
                      & models.Q(number_of_episodes__gte=1)
            ),
            #  Number_of_episodes >= last_watched_episode
            models.CheckConstraint(
                name='mutual_watched_episode_and_number_of_episodes_check',
                check=(models.Q(number_of_episodes__gte=models.F('last_watched_episode')))
            ),
            #  season_number >= 1
            models.CheckConstraint(
                name='season_number_gte_1_check',
                check=models.Q(season_number__gte=1),
            )
        ]

    def __str__(self):
        return f'season number - {self.season_number}, series name - {self.series.name}'

    # todo
    @cached_property
    def get_absolute_url(self):
        raise NotImplementedError

    def clean(self):
        errors = {}

        #  Check if last_watched_episode number is bigger then number of episodes in season.
        if self.last_watched_episode and (self.last_watched_episode > self.number_of_episodes):
            errors.update(
                {'last_watched_episode': exceptions.ValidationError(
                    f'Last watched episode number {self.last_watched_episode}'
                    f' is greater then number of episodes {self.number_of_episodes}'
                    f' in the whole season!!!', code='mutual_validation_out_of_range')}
            )
        # if we have a key in JSON data in episodes field with number greater then number of episodes in season.
        # 1) Filter only positive digits from JSON keys()
        if self.episodes:
            _episodes = MappingProxyType(self.episodes or {})
            list_of_legit_episodes_keys = custom_functions.filter_positive_int_or_digit(_episodes.keys())
            # 2) Get key with max. value from all present keys. If it is empty we use zero as zero is always smaller
            # then any legit number of episodes.
            max_key = heapq.nlargest(1, list_of_legit_episodes_keys)
            # 3) Needles to explain further...
            if max_key and (max_key[0] > self.number_of_episodes):
                errors.update(
                    {'episodes': exceptions.ValidationError(
                        f'Episode number {max_key[0]} in "episodes" '
                        f' field is greater then number of episodes '
                        f'{self.number_of_episodes}',
                        code='mutual_validation_out_of_range')}
                )
        if errors:
            raise exceptions.ValidationError(errors)

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
        try:
            # episode number key might be in str or int format. We trying to get it as a str and then as a int.
            try:
                last_episode_release_date = self.episodes[str(self.number_of_episodes)]
            except KeyError:
                last_episode_release_date = self.episodes[self.number_of_episodes]
        # if 'episodes' field is None or there are no key == 'number_of_episodes'.
        except (KeyError, TypeError):
            return None

        now = timezone.now().timestamp()
        return now > last_episode_release_date


class ImageModelMetaClass(type(models.Model)):
    """
    Metaclass for ImageModel.
    """

    def __getattr__(cls, attrname):
        if attrname == 'stored_image_hash':
            setattr(cls, attrname, cls.get_image_hash_from_db())
            return getattr(cls, attrname)
        else:
            return super().__getattr__(attrname)


class ImageModel(models.Model, metaclass=ImageModelMetaClass):
    """
    Model represents an image. Can be attached to any model in the project.
    Based on a Generic FK.
    """
    objects = archives.managers.ImageManager.from_queryset(archives.managers.ImageQueryset)()

    image = models.ImageField(
        upload_to=file_uploads.save_image_path,
        verbose_name='An image',
        validators=[custom_validators.IsImageValidator(), ],
    )
    image_hash = custom_fields.ImageHashField(
        max_length=16,
        null=True,
        blank=True,
        verbose_name='Image hash.',
        unique=True,
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

    class Meta:
        verbose_name = 'Image'
        verbose_name_plural = 'Images'
        constraints = [
            models.CheckConstraint(
                name='len_16_constraint',
                check=models.Q(image_hash__length=16),
            ), ]

    def __str__(self):
        return f'image - {self.image.name}, model - {self.content_type} - pk={self.object_id}'

    def clean(self):
        #  I instance has not image hash yet - try to generate and set hash to it.
        if self.image_hash is None:
            self.image_hash = self.make_image_hash()
        # If hash is still None or this instance has already it image_hash stored in class attribute -
        # - skip validation then.
        if self.image_hash is None or (self.pk in self.__class__.stored_image_hash.keys()):
            return None
        # If image hash has Hamming difference les then X - raise validation error as this or closer
        # to this image already exists in DB.
        for img_hash in self.__class__.stored_image_hash.values():
            if (img_hash - self.image_hash) < 10:
                raise exceptions.ValidationError(
                    {'image': error_codes.IMAGE_ALREADY_EXISTS.message},
                    code=error_codes.IMAGE_ALREADY_EXISTS.code,
                )

    def save(self, fc=True, *args, **kwargs):
        """
        image instance - ImageFieldFile, django.db.models.fields.files.
        """
        #  'image_hash' assigment should take place after 'full_clean' as 'make_image_hash' empties
        #  file stream iterator and validator in 'full_clean' receives empty iterator, which it can not
        #  validate successfully.

        if fc:
            self.full_clean(exclude=('image_hash',))

        if not self.image_hash:
            self.image_hash = self.make_image_hash()

        super().save(*args, **kwargs)
        self.image.close()
        self.__class__.stored_image_hash[self.pk] = self.image_hash

    def delete(self, using=None, keep_parents=False):
        deleted = super().delete(using, keep_parents)
        self.delete_stored_image_hash(pk=self.pk)
        return deleted

    @classmethod
    def delete_stored_image_hash(cls, pk: int) -> None:
        """
        Deletes stored image hash if exists.
        """
        try:
            del cls.stored_image_hash[pk]
        except (AttributeError, KeyError):
            pass

    @property
    def image_file_name(self):
        """
        Returns name of the image file.
        """
        return os.path.basename(self.image.file.name)

    def make_image_hash(self):
        """
        Makes hash for image file.
        """
        image_hash = custom_functions.create_image_hash(self.image.open('rb'))
        return image_hash

    @classmethod
    def get_image_hash_from_db(cls):
        """
        Fetch all ImageModel instances pk and image_hash from DB.
        """
        image_hash_from_db = cls.objects.exclude(image_hash__isnull=True).values_list('pk', 'image_hash', )
        return IOBTree(image_hash_from_db)
