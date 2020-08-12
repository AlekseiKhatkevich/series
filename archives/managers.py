import datetime
from typing import List

import guardian.models
import more_itertools
from django.contrib.postgres.aggregates import BoolAnd, StringAgg
from django.db import models
from django.db.models import Case, CharField, F, FloatField, Max, Min, OuterRef, Q, Subquery, When, functions
from psycopg2.extras import DateRange

from series import error_codes
from series.constants import DEFAULT_OBJECT_LEVEL_PERMISSION_CODE


class TvSeriesQueryset(models.QuerySet):
    """
    TvSeries model custom queryset.
    """

    def select_x_percent(self, percent: int, position: str) -> models.QuerySet:
        """
        Returns top or bottom x % of Tv series according their rating.
        """
        rating_max = Max('rating', output_field=FloatField())
        rating_min = Min('rating', output_field=FloatField())
        one_percent = (rating_max - rating_min) / 100.0
        choices, *rest = more_itertools.unzip(self.model._meta.get_field('rating').choices)
        filtered_choices = tuple(filter(None.__ne__, choices))
        min_choice, max_choice = min(filtered_choices), max(filtered_choices)

        if position == 'top':
            condition = dict(
                rating__gte=self.aggregate(
                    lvl=functions.Coalesce(rating_max - (one_percent * float(percent)), min_choice)
                )['lvl'],
            )
        elif position == 'bottom':
            condition = dict(
                rating__lte=self.aggregate(
                    lvl=functions.Coalesce(rating_min + (one_percent * float(percent)), max_choice)
                )['lvl'],
            )
        else:
            raise ValueError(
                *error_codes.SELECT_X_PERCENT
            )

        return self.filter(**condition).order_by('rating')

    def running_series(self) -> models.QuerySet:
        """
        Returns only not finished series.
        """
        return self.exclude(translation_years__fully_lt=DateRange(datetime.date.today(), None))

    def finished_series(self) -> models.QuerySet:
        """
        Returns only finished series.
        """
        return self.filter(translation_years__fully_lt=DateRange(datetime.date.today(), None))

    def annotate_with_responsible_user(self):
        """
        Annotates queryset with 'responsible' ,which is email of the user who is responsible
        for this series.
        """
        annotations = dict(
            responsible=Case(
                #  If entry author is not soft deleted.
                When(
                    entry_author__deleted=False,
                    then=F('entry_author__email')
                ),
                # If entry author is soft-deleted but has master alive.
                When(
                    entry_author__master__isnull=False, entry_author__master__deleted=False,
                    then=F('entry_author__master__email')
                ),
                # If entry author is soft-deleted, hasn't master alive but has alive slaves.
                When(
                    # when not [author is deleted(True) == all slaves are deleted(False)]
                    ~Q(entry_author__deleted=BoolAnd('entry_author__slaves__deleted')),
                    then=StringAgg(
                        'entry_author__slaves__email',
                        distinct=True,
                        delimiter=', ',
                        filter=Q(entry_author__slaves__deleted=False)
                    )),
                #  When user is soft-deleted and does not have alive master or slaves but has friends with objects
                #  permission on this series alive.
                #  https://stackoverflow.com/questions/63020407/return-multiple-values-in-subquery-in-django-orm
                default=Subquery(
                    guardian.models.UserObjectPermission.objects.filter(
                        object_pk=functions.Cast(OuterRef('id'), CharField()),
                        content_type__model=self.model.__name__.lower(),
                        content_type__app_label=self.model._meta.app_label.lower(),
                        permission__codename=DEFAULT_OBJECT_LEVEL_PERMISSION_CODE,
                        user__deleted=False,
                    ).values('object_pk').annotate(
                        emails=StringAgg('user__email', ', ', distinct=True)
                    ).values('emails')
                )))

        return self.annotate(**annotations)


class TvSeriesManager(models.Manager):
    """
    TvSeries model custom manager.
    """
    pass


# -----------------------------------------------------------------------------------
class EmptyTvSeriesQueryset(TvSeriesQueryset):
    """
    EmptyTVSeriesModel custom queryset.
    """
    pass


class EmptyTvSeriesManager(TvSeriesManager):
    """
    EmptyTVSeriesModel model custom manager.
    """

    def get_queryset(self):
        """
        Returns only series with no seasons (empty series).
        """
        return super().get_queryset().filter(seasons__isnull=True)

# -----------------------------------------------------------------------------------


class SeasonQueryset(models.QuerySet):
    """
    SeasonModel custom queryset.
    """
    pass


class SeasonManager(models.Manager):
    """
    SeasonModel custom manager.
    """
    pass


# -----------------------------------------------------------------------------------


class ImageQueryset(models.QuerySet):
    """
    ImageModel custom queryset.
    """

    def create(self, fc: bool = True, **kwargs) -> models.Model:
        """
        Add 'fc' option to switch off/on full_clean() model method on save().
        """
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, fc=fc)
        return obj


class ImageManager(models.Manager):
    """
    ImageModel custom manager.
    """
    pass


# -----------------------------------------------------------------------------------

class GroupingManager(models.Manager):
    """
    GroupingModel custom manager.
    """

    def create_relation_pair(
            self,
            from_series: models.Model,
            to_series: models.Model,
            reason_for_interrelationship: str,
            *,
            save_in_db: bool = False,
            ignore_conflicts: bool = False,
    ) -> List[models.Model]:
        """
        Creates pair of relations (form series A to series B) and (form series B to series A).
        """
        resulting_pair = []

        seq = (from_series, to_series)
        for num, _ in enumerate(seq):
            resulting_pair.append(self.model(
                from_series=seq[num],
                to_series=seq[not num],
                reason_for_interrelationship=reason_for_interrelationship,
            ))
        if save_in_db:
            return self.bulk_create(
                resulting_pair,
                ignore_conflicts=ignore_conflicts,
            )
        return resulting_pair


class GroupingQueryset(models.QuerySet):
    """
    GroupingModel custom queryset.
    """
    pass

# -----------------------------------------------------------------------------------
