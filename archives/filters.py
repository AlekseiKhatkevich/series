import datetime

from django_filters import rest_framework as rest_framework_filters, widgets, fields
from psycopg2.extras import DateRange

import archives.models


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
    def finished(queryset, field_name, value):
        """
        Returns finished series if value=True and running series if value=False.
        """
        now = datetime.date.today()
        condition = {f'{field_name}__fully_lt': DateRange(now, None)}

        return queryset.filter(**condition) if value else queryset.exclude(**condition)
