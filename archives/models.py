import datetime
import os
from collections import defaultdict
from fractions import Fraction
from typing import KeysView, Optional, Tuple, Union

import more_itertools
from BTrees.IOBTree import IOBTree
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres import constraints as psgr_constraints, fields as psgr_fields, \
    indexes as psgr_indexes
from django.core import exceptions, validators
from django.db import models
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property
from psycopg2.extras import DateRange
from rest_framework.reverse import reverse

import archives.managers
from archives.helpers import custom_fields, custom_functions, file_uploads, validators as custom_validators
from series import constants, error_codes
from series.helpers.custom_functions import available_range


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
        related_query_name='series',
    )
    access_logs = GenericRelation(
        'administration.EntriesChangeLog',
        related_query_name='series',
    )

    entry_author = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='series',
        verbose_name='Author of the series entry',
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
        unique=True,
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
                message='Maximal value for this field is 10',
            )])
    translation_years = psgr_fields.DateRangeField(
        verbose_name='Series years of translation.',
        validators=[
            custom_validators.DateRangeValidator(upper_inf_allowed=True)
        ], )

    class Meta:
        verbose_name = 'series'
        verbose_name_plural = 'series'
        permissions = (
            ('permissiveness', 'Allow any action',),
        )
        indexes = [
            psgr_indexes.GistIndex(fields=('translation_years',), ),
        ]
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
            if not self._state.adding and ('imdb_url' not in self.changed_fields):
                exclude = ('imdb_url',)
            else:
                exclude = ()

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
        now = timezone.now().date()
        infinity = timezone.datetime.max.date()
        upper_bound = self.translation_years.upper

        return now > (upper_bound or infinity)

    @property
    def is_empty(self):
        """
        Returns True if series does not have any season associated with it.
        """
        return not self.seasons.exists()


class SeasonModel(models.Model):
    """
    Model represents one singular season of a series.
    """
    access_logs = GenericRelation(
        'administration.EntriesChangeLog',
        related_query_name='seasons',
    )

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
    entry_author = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='seasons',
        verbose_name='Author of the season.',
    )
    season_number = models.PositiveSmallIntegerField(
        verbose_name='Number of the current season',
        default=1,
        validators=[
            non_zero_validator,
            validators.MaxValueValidator(30),
        ], )
    last_watched_episode = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        verbose_name='Last watched episode of a current season',
        validators=[
            custom_validators.skip_if_none_none_zero_positive_validator,
        ], )
    number_of_episodes = models.PositiveSmallIntegerField(
        verbose_name='Number of episodes in the current season',
        validators=[
            non_zero_validator,
            validators.MaxValueValidator(30),
        ], )
    episodes = custom_fields.CustomHStoreField(
        null=True,
        blank=True,
        verbose_name='Episode number and issue date',
        # Validator has moved to clean(). Do not move it back!
    )
    translation_years = psgr_fields.DateRangeField(
        verbose_name='Season years of translation.',
        validators=[
            custom_validators.DateRangeValidator()
        ], )

    class Meta:
        order_with_respect_to = 'series'
        unique_together = (
            ('series', 'season_number',),
        )
        permissions = (
            ('permissiveness', 'Allow any action',),
        )
        index_together = unique_together
        verbose_name = 'Season'
        verbose_name_plural = 'Seasons'
        indexes = [
            psgr_indexes.GistIndex(fields=('translation_years',), ),
        ]
        constraints = [
            # (Last_watched_episodes >= 1 or None) and number_of_episodes in range(1, 30).
            models.CheckConstraint(
                name='last_watched_episode_and_number_of_episodes_are_gte_one',
                check=(models.Q(last_watched_episode__gte=1) | models.Q(last_watched_episode__isnull=True))
                      & models.Q(number_of_episodes__range=(1, 30))
            ),
            #  Number_of_episodes >= last_watched_episode
            models.CheckConstraint(
                name='mutual_watched_episode_and_number_of_episodes_check',
                check=(models.Q(number_of_episodes__gte=models.F('last_watched_episode')))
            ),
            #  Season_number >= 1
            models.CheckConstraint(
                name='season_number_gte_1_check',
                check=models.Q(season_number__range=(1, 30)),
            ),
            # Season translation years can not overlap each other.
            psgr_constraints.ExclusionConstraint(
                name='exclude_overlapping_seasons_translation_time_check',
                expressions=[
                    ('translation_years', psgr_fields.RangeOperators.OVERLAPS),
                    ('series', psgr_fields.RangeOperators.EQUAL),
                ], ),
            # Season maximal range is one year. Fake constraint. Real one in migration file 0053.
            models.CheckConstraint(
                name='max_range_one_year',
                check=models.Q(translation_years__contained_by=datetime.timedelta(days=366))
            ),
            #  Maximal key in episodes should be lte than 'number_of_episodes'. Fake constraint.
            #  Real constraint in migration file 0055_hstore_constraint.
            models.CheckConstraint(
                name='max_key_lte_number_of_episodes',
                check=models.Q(episodes__has_any_keys__gt=models.F('number_of_episodes'))
            ),
            #  Episodes dates should be within series translation_years. fake constraint. Real one
            #  in migration file 0056_episodes_in_season_constraint.
            models.CheckConstraint(
                name='episodes_within_season_check',
                check=models.Q(
                    episodes__values__gte=models.Func(
                        models.Min(models.F('translation_years')),
                        function='LOWER',
                    )) &
                      models.Q(
                          episodes__values__lte=models.Func(
                              models.Max(models.F('translation_years')),
                              function='UPPER',
                          ))),
            #  Episodes keys and dates should be ordered by both keys and dates. Uses custom transform
            #  'check_episodes'.
            models.CheckConstraint(
                name='episodes_sequence_check',
                check=models.Q(episodes__check_episodes=True),
            )]

    def __str__(self):
        return f'pk - {self.pk}, season number - {self.season_number}, series name - {self.series.name}'

    @cached_property
    def get_absolute_url(self):
        return reverse(
            f'{self.__class__._meta.model_name}-detail',
            args=(self.series_id, self.pk),
        )

    def clean(self):
        errors = defaultdict(list)
        current_series = self.series

        #  Check if last_watched_episode number is bigger then number of episodes in season.
        if self.last_watched_episode and (self.last_watched_episode > self.number_of_episodes):
            errors['last_watched_episode'].append(exceptions.ValidationError(
                *error_codes.LAST_WATCHED_GTE_NUM_EPISODES
            ))

        #  Check that season translation years should be within series range.
        if not ((self.translation_years.lower in current_series.translation_years) and
                (self.translation_years.upper in current_series.translation_years)):
            errors['translation_years'].append(exceptions.ValidationError(
                *error_codes.SEASON_NOT_IN_SERIES
            ))

        # Check if translation years of season within series are not overlap each other.
        if self._meta.model.objects.filter(
                series=current_series,
                translation_years__overlap=self.translation_years,
        ).exclude(pk=self.pk).exists():
            errors['translation_years'].append(exceptions.ValidationError(
                *error_codes.SEASONS_OVERLAP,
            ))

        # Check that translation years date ranges of season in series are greater one another
        # successively.
        if self._meta.model.objects.filter(
                models.Exists(
                    self._meta.model.objects.filter(
                        translation_years__gt=models.OuterRef('translation_years'),
                        season_number__lt=models.OuterRef('season_number'),
                        series=current_series,
                    ), ), ).exists():
            errors['translation_years'].append(exceptions.ValidationError(
                *error_codes.TRANSLATION_YEARS_NOT_ARRANGED
            ))

        #  Check that season translation years range less then one year.
        if (self.translation_years.upper - self.translation_years.lower).days > 365:
            errors['translation_years'].append(exceptions.ValidationError(
                *error_codes.SEASON_TY_GT_YEAR
            ))

        if self.episodes is not None:

            # If schema is incorrect we need to stop it right now without proceeding further.
            custom_validators.ValidateDict(schema=custom_validators.episode_date_schema)(self.episodes)

            # Maximal number of episodes in episodes should be lte than number of episodes.
            max_key = max(self.episodes.keys())
            if max_key > self.number_of_episodes:
                errors['episodes'].append(exceptions.ValidationError(
                    *error_codes.MAX_KEY_GT_NUM_EPISODES
                ))

            # Dates in episodes should be gte each other in succession.
            # We sort dict by keys and then check whether dates are sorted (prev. <= lat.)
            sorted_by_episodes_numbers = dict(sorted(self.episodes.items()))
            are_dates_sorted = more_itertools.is_sorted(sorted_by_episodes_numbers.values())
            if not are_dates_sorted:
                errors['episodes'].append(exceptions.ValidationError(
                    *error_codes.EPISODES_DATES_NOT_SORTED
                ))

            # Max and Min dates in episodes should lay within season translation years daterange.
            min_date, max_date = min(self.episodes.values()), max(self.episodes.values())
            if (min_date not in self.translation_years) or (max_date not in self.translation_years):
                errors['episodes'].append(exceptions.ValidationError(
                    *error_codes.EPISODES_NOT_IN_RANGE
                ))

        if errors:
            raise exceptions.ValidationError(errors)

    def save(self, fc=True, *args, **kwargs):
        if fc:
            self.full_clean(validate_unique=True)
        super().save(*args, **kwargs)

    @property
    def is_fully_watched(self) -> bool:
        """
        Is current season are fully watched by user?
        """
        return self.last_watched_episode == self.number_of_episodes

    @property
    def is_finished(self) -> bool:
        """
        Returns whether current season is finished or not.
        """
        return TvSeriesModel.is_finished.fget(self)

    @property
    def progress(self) -> Fraction:
        """
        Returns season watch progress as Fraction instance.
        """
        return Fraction(
            self.last_watched_episode or 0,
            self.number_of_episodes,
        )

    @property
    def new_episode_this_week(self) -> Optional[Union[Tuple[datetime.date], bool]]:
        """
        Returns a dates of the episodes if there are one or few this week or False in opposite way.
        Returns None in case empty 'episodes' field.
        """
        if not self.episodes:
            return None

        first_day_of_week = (dt := datetime.date.today()) - datetime.timedelta(days=dt.weekday())
        last_day_of_week = first_day_of_week + datetime.timedelta(days=6)

        return tuple(
            date for date in self.episodes.values() if first_day_of_week <= date <= last_day_of_week
        ) or False

    @property
    def season_available_range(self):
        """
        Returns daterange allowed by all validators for the season.
        """
        cls = self.__class__
        series_range = self.series.translation_years
        # Seasons with next and previous numbers.
        next_gt_season = cls.objects.filter(
            series=self.series,
            season_number__gt=self.season_number
        ).order_by('season_number')[:1]
        next_lt_season = cls.objects.filter(
            series=self.series,
            season_number__lt=self.season_number
        ).order_by('-season_number')[:1]
        # date ranges of 2 seasons together.
        two_adjacent_seasons = next_gt_season.union(next_lt_season).values_list(
            'season_number',
            'translation_years',
            named=True,
        )
        inner_ranges = []
        effective_infinity = datetime.date(datetime.date.today().year + 2, 1, 1)
        #  Extend date ranges of 2 adjacent seasons to low and upper of series range.
        for date_range in two_adjacent_seasons:
            if date_range.season_number < self.season_number:
                inner_ranges.append(DateRange(
                    series_range.lower,
                    date_range.translation_years.upper
                ))
            else:
                inner_ranges.append(DateRange(
                    date_range.translation_years.lower,
                    series_range.upper or effective_infinity
                ))
        return available_range(series_range, *inner_ranges)[0]


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
    access_logs = GenericRelation(
        'administration.EntriesChangeLog',
        related_query_name='images',
    )

    objects = archives.managers.ImageManager.from_queryset(archives.managers.ImageQueryset)()

    entry_author = models.ForeignKey(
        get_user_model(),
        on_delete=models.PROTECT,
        related_name='images',
        verbose_name='Author of the image.',
    )

    image = models.ImageField(
        upload_to=file_uploads.save_image_path,
        verbose_name='An image',
        validators=[
            custom_validators.IsImageValidator(),
        ], )
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
            if img_hash is not None and (img_hash - self.image_hash) < 10:
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
            self.full_clean(exclude=('image_hash',), validate_unique=True)

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

