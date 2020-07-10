import datetime

from django_filters import fields, rest_framework as rest_framework_filters, widgets
from psycopg2.extras import DateRange
from django.db.models import F, Q
import archives.models

queryset_instance = archives.models.models.QuerySet


class DateExactRangeWidget(widgets.DateRangeWidget):
    """
    Date widget to help filter by *_lower and *_upper.
    """
    suffixes = ['lower', 'upper']


class DateExactRangeField(fields.DateRangeField):
    """
    Custom field to combine daterange from 2 input values: lower bound and upper bound.
    """
    widget = DateExactRangeWidget

    def compress(self, data_list):
        if data_list:
            lower_bound, upper_bound = data_list
            return DateRange(
                datetime.date.fromisoformat(str(lower_bound)) if lower_bound is not None else None,
                datetime.date.fromisoformat(str(upper_bound)) if upper_bound is not None else None
            )


class DateExactRangeFilter(rest_framework_filters.Filter):
    """
    Filter to be used for Postgres specific Django field - DateRangeField.
    """
    field_class = DateExactRangeField


class TvSeriesListCreateViewFilter(rest_framework_filters.FilterSet):
    """
    Filter for 'TvSeriesListCreateView'.
    """
    is_empty = rest_framework_filters.BooleanFilter(
        field_name='seasons_cnt',
        lookup_expr='isnull',
        label='Is series empty?',
    )
    seasons_cnt__lte = rest_framework_filters.NumberFilter(
        field_name='seasons_cnt',
        lookup_expr='lte',
        label='Number of seasons in series lte...',
    )
    seasons_cnt__gte = rest_framework_filters.NumberFilter(
        field_name='seasons_cnt',
        lookup_expr='gte',
        label='Number of seasons in series gte...',
    )
    is_finished = rest_framework_filters.BooleanFilter(
        field_name='translation_years',
        label='Yes - return only finished series, No - return only running series.',
        method='finished',
    )
    translation_years_contained_by = DateExactRangeFilter(
        field_name='translation_years',
        lookup_expr='contained_by',
    )
    translation_years_overlap = DateExactRangeFilter(
        field_name='translation_years',
        lookup_expr='overlap',
    )

    class Meta:
        model = archives.models.TvSeriesModel
        fields = {
            'entry_author__email': ['exact'],
            'entry_author__first_name': ['iexact'],
            'entry_author__last_name': ['iexact'],
            'entry_author__deleted': ['exact'],
            'name': ['exact'],
            'rating': ['lte', 'gte', ],
        }

    @staticmethod
    def finished(queryset: queryset_instance, field_name: str, value: DateRange) -> queryset_instance:
        """
        Returns finished series if value=True and running series if value=False.
        """
        now = datetime.date.today()
        condition = {f'{field_name}__fully_lt': DateRange(now, None)}

        return queryset.filter(**condition) if value else queryset.exclude(**condition)


class SeasonsFilterSet(rest_framework_filters.FilterSet):
    """
    Filter for 'SeasonsViewSet' list action.
    """
    episodes = rest_framework_filters.BooleanFilter(
        field_name='episodes',
        lookup_expr='isnull',
        label='Are season episodes empty?',
    )
    episodes_dates = DateExactRangeFilter(
        field_name='episodes',
        label='Episodes dates contains dates within this range.',
        method='filter_episodes_dates',
    )
    translation_years_contained_by = DateExactRangeFilter(
        field_name='translation_years',
        lookup_expr='contained_by',
    )
    translation_years_overlap = DateExactRangeFilter(
        field_name='translation_years',
        lookup_expr='overlap',
    )
    filter_by_user = rest_framework_filters.BooleanFilter(
        field_name='series__entry_author',
        method='show_only_mine',
        label='YES - Show only seasons created by you, NO - created by someone else but you.',
    )
    # is_fully_watched = rest_framework_filters.BooleanFilter(
    #     field_name='last_watched_episode',
    #     method='show_only_mine',
    #     label='YES - shows only fully watched seasons, NO - shows only not fully watched seasons.',
    # )

    class Meta:
        model = archives.models.SeasonModel
        fields = {
            'season_number': ['lte', 'gte', ],
            'number_of_episodes': ['lte', 'gte', ],
        }

    # @staticmethod
    # def fully_watched(
    #         queryset: queryset_instance,
    #         field_name: str,
    #         value: bool
    # ) -> queryset_instance:
    #     """
    #     Returns seasons filtered by whether they have been fully watched or not.
    #     """
    #     #condition = {field_name: F('number_of_episodes')}
    #
    #     return queryset.filter(Q(last_watched_episode__gte=F('number_of_episodes'))) #if value else queryset.exclude(**condition)

    @staticmethod
    def filter_episodes_dates(
            queryset: queryset_instance,
            field_name: str,
            value: DateRange
    ) -> queryset_instance:
        """
        Returns seasons that have episodes dates in the chosen range.
        """
        lower = f"'{value.lower}'" if value.lower else 'null'
        upper = f"'{value.upper}'" if value.upper else 'null'
        return queryset.extra(
            where=[f"daterange({lower}, {upper}, '[]') @> any(avals({field_name})::date[])"]
        )

    def show_only_mine(
            self,
            queryset: queryset_instance,
            field_name: str,
            value: bool
    ) -> queryset_instance:
        """
        Returns qs filtered by whether current user is a creator of a series.
        """
        condition = {field_name: self.request.user}

        return queryset.filter(**condition) if value else queryset.exclude(**condition)
