import datetime

import guardian.models
from django import forms
from django.core import exceptions
from django.db.models import BooleanField, ExpressionWrapper, F, FloatField, Q
from django.db.models.functions import Cast
from django_filters import fields, rest_framework as rest_framework_filters, widgets
from psycopg2.extras import DateRange

import archives.models
import archives.serializers
from series import error_codes

queryset_instance = archives.models.models.QuerySet


class TopBottomPercentWidget(widgets.SuffixedMultiWidget):
    """
    Widget for TopBottomPercentField. Accept positions (top or bottom) as first suffix
    and int percent as second suffix.
    """
    suffixes = ['position', 'percent']

    def __init__(self, attrs=None):
        widgets = (forms.TextInput, forms.NumberInput)
        super().__init__(widgets, attrs)


class TopBottomPercentField(fields.RangeField):
    """
    Field for TopBottomPercentFilter. Compresses position and percent values into a dict.
    """
    widget = TopBottomPercentWidget

    def __init__(self, *args, **kwargs):
        fields = (
            forms.ChoiceField(choices=(('top', 'top',), ('bottom', 'bottom',))),
            forms.IntegerField(min_value=1, max_value=99)
        )
        super().__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        if data_list:
            return {'position': data_list[0], 'percent': data_list[1]}

        return None

    def clean(self, value):
        """
        Check that both position and percent are present or omitted in data.
        """
        if value.count('') == 1:
            raise exceptions.ValidationError(
                *error_codes.SELECT_X_PERCENT_FIELD,
            )

        return super().clean(value)


class TopBottomPercentFilter(rest_framework_filters.Filter):
    """
    Filter to be used for Postgres specific Django field - DateRangeField.
    """
    field_class = TopBottomPercentField


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
    series_percent = TopBottomPercentFilter(
        method='x_percent',
        label='Select top or bottom x percent.',
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
    def x_percent(queryset: queryset_instance, field_name: str, value: dict) -> queryset_instance:
        """
        Returns queryset filtered by top or bottom % ratings values.
        """
        try:
            position = value['position']
            percent = value['percent']
        except KeyError:
            return queryset

        return queryset.select_x_percent(percent=percent, position=position)

    @staticmethod
    def finished(queryset: queryset_instance, field_name: str, value: bool) -> queryset_instance:
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
        field_name='entry_author',
        method='show_only_mine',
        label='YES - shows only seasons created by you, NO - created by someone else but you.',
    )
    is_fully_watched = rest_framework_filters.BooleanFilter(
        field_name='last_watched_episode',
        label='YES - shows only fully-watched seasons, NO - shows only non-fully-watched seasons.',
        method='fully_watched',
    )
    is_finished = rest_framework_filters.BooleanFilter(
        field_name='translation_years',
        label='Yes - return only finished series, No - return only running series.',
        method='finished',
    )
    has_episodes_this_week = rest_framework_filters.BooleanFilter(
        field_name='episodes',
        method='filter_with_episodes_this_week',
        label='Yes - shows only seasons which has episodes this week,'
              ' NO -seasons without episodes this week.'
    )
    progress_lte = rest_framework_filters.NumberFilter(
        field_name='progr__lte',
        method='filter_by_progress',
        label='Watch progress lte than value.',
    )
    progress_gte = rest_framework_filters.NumberFilter(
        field_name='progr__gte',
        method='filter_by_progress',
        label='Watch progress gte than value.',
    )

    class Meta:
        model = archives.models.SeasonModel
        fields = {
            'season_number': ['lte', 'gte', ],
            'number_of_episodes': ['lte', 'gte', ],
        }

    @staticmethod
    def filter_by_progress(
            queryset: queryset_instance,
            field_name: str,
            value: float,
    ) -> queryset_instance:
        """
        Filters by watch progress ('last_watched_episode' / 'number_of_episodes')
        """
        return queryset.annotate(
                progr=(ExpressionWrapper(
                    Cast('last_watched_episode', output_field=FloatField()) /
                    Cast('number_of_episodes', output_field=FloatField()),
                    output_field=FloatField()
                ))).filter(**{field_name: value})

    @staticmethod
    def finished(queryset: queryset_instance, field_name: str, value: bool) -> queryset_instance:
        """
        Returns only finished or non-finished seasons.
        """
        return TvSeriesListCreateViewFilter.finished(queryset, field_name, value)

    @staticmethod
    def fully_watched(queryset: queryset_instance, field_name: str, value: bool) -> queryset_instance:
        """
        Returns only fully watched or non-fully-watched seasons.
        """
        expression = ExpressionWrapper(
            Q(last_watched_episode=F('number_of_episodes')),
            output_field=BooleanField()
        )
        return queryset.filter(expression) if value else queryset.exclude(expression)

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

    @staticmethod
    def filter_with_episodes_this_week(
            queryset: queryset_instance,
            field_name: str,
            value: DateRange
    ) -> queryset_instance:
        """
        Returns series that have episodes this week or opposite.
        """
        raw_sql = f"""
                    daterange(
                    date_trunc('week', current_date)::date,
                    date_trunc('week', current_date + interval '1 week')::date,
                    '[]'
                    ) @> any(avals({field_name})::date[])
                    """
        if not value:
            raw_sql = 'not ' + raw_sql

        return queryset.extra(where=[raw_sql])

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


class UserObjectPermissionFilterSet(rest_framework_filters.FilterSet):
    """
    Filterset for  user object permission list view archives/manage-permissions/.
    """
    model = progress_gte = rest_framework_filters.MultipleChoiceFilter(
        field_name='content_type__model',
        choices=archives.serializers.ManagePermissionsSerializer.MODEL_CHOICES.choices,
    )

    class Meta:
        model = guardian.models.UserObjectPermission
        fields = {
            'object_pk': ['exact', ],
            'id': ['exact', ],
            'user__email': ['iexact', ],
        }

