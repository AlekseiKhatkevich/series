from django.db.models import PositiveSmallIntegerField, TextChoices
from django_db_logger.models import LOG_LEVELS, StatusLog
from django_filters import rest_framework as rest_framework_filters

import administration.models


class LogsFilterSet(rest_framework_filters.FilterSet):
    """
    Filter for LogsListView.
    """

    class LOGGERS_CHOICES(TextChoices):
        REQUEST = 'django.request', 'django.request'
        SERVER = 'django.server', 'django.server'
        TEMPLATE = 'django.template', 'django.template'
        DB_BACKENDS = 'django.db.backends', 'django.db.backends'
        SECURITY = 'django.security', 'django.security'
        BACKENDS_SCHEMA = 'django.db.backends.schema', 'django.db.backends.schema'

    logger_name = rest_framework_filters.ChoiceFilter(
        field_name='logger_name',
        choices=LOGGERS_CHOICES.choices,
        lookup_expr='startswith',
    )

    class Meta:
        model = StatusLog
        fields = {
            'level': ['gte', 'lte', ],
            'create_datetime': ['gte', 'lte', ]
        }
        filter_overrides = {
            PositiveSmallIntegerField: {
                'filter_class': rest_framework_filters.ChoiceFilter,
                'extra': lambda f: {
                    'choices': LOG_LEVELS,
                }, }}


class HistoryViewSetFilterSet(rest_framework_filters.FilterSet):
    """
    Filter for 'HistoryViewSet'.
    """
    as_who = rest_framework_filters.ChoiceFilter(
        field_name='as_who',
        choices=administration.models.UserStatusChoices.choices,
        lookup_expr='iexact',
    )
    operation_type = rest_framework_filters.ChoiceFilter(
        field_name='operation_type',
        choices=administration.models.OperationTypeChoices.choices,
        lookup_expr='iexact',
    )

    class Meta:
        model = administration.models.EntriesChangeLog
        fields = {
            'access_time': ['gte', 'lte', ],
        }
