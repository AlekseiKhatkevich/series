from django.db import models
from django.db.models import Min, Max, FloatField
from django.db.models.functions import Floor, Ceil


class TvSeriesQueryset(models.QuerySet):
    """
    TvSeries model custom queryset.
    """
    def top_x_percent(self, percent: int) -> models.QuerySet:
        """
        Returns top x % of Tv series according their rating.
        """
        result = self.aggregate(
            Min('rating', output_field=FloatField()),
            Max('rating', output_field=FloatField()),
        )
        percent_value = (result['rating__max'] - result['rating__min']) / 100
        top_range = (
            Ceil(result['rating__max'] - (percent * percent_value)),
            Floor(result['rating__max'])
        )
        return self.filter(rating__range=top_range)

    def running_series(self):
        """
        Returns only not finished series.
        """
        return self.exclude(is_finished=True)


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
