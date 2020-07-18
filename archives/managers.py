import datetime
from typing import List

from django.db import models
from django.db.models import FloatField, Max, Min
from psycopg2.extras import DateRange

from series import error_codes


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

        if position == 'top':
            condition = dict(
                rating__gte=self.aggregate(
                    lvl=rating_max - (one_percent * float(percent))
                )['lvl'],
            )
        elif position == 'bottom':
            condition = dict(
                rating__lte=self.aggregate(
                    lvl=rating_min + (one_percent * float(percent))
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


class TvSeriesManager(models.Manager):
    """
    TvSeries model custom manager.
    """
    pass


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
