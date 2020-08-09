from django.contrib.auth import get_user_model
from django.db.models import Exists, Max, OuterRef, QuerySet, Subquery, TextChoices
from django_filters import rest_framework as rest_framework_filters

import administration.models
import archives.models


class UsersListFilter(rest_framework_filters.FilterSet):
    """
    Filter for 'UserViewSet' viewset list action.
    """

    slaves = rest_framework_filters.BooleanFilter(
        field_name='master',
        lookup_expr='isnull',
        label='Yes - show only slaves, No - show non-slaves',
        exclude=True,
    )
    masters = rest_framework_filters.BooleanFilter(
        field_name='master',
        method='show_masters',
        label='Yes - show only masters, No - show non-masters.',
    )

    class Meta:
        model = get_user_model()
        fields = {
            'first_name': ['iexact'],
            'last_name': ['iexact'],
            'master__email': ['exact'],
            'slaves__email': ['exact'],
            'deleted': ['exact'],
            'email': ['exact'],
            'user_country': ['exact'],
        }

    @staticmethod
    def show_masters(queryset: QuerySet, field_name: str, value: bool) -> QuerySet:
        """
        Returns masters if value = True and non-masters if value = False.
        """
        has_slaves = Exists(queryset.filter(master_id=OuterRef('pk')))
        queryset_of_masters = queryset.filter(has_slaves)
        queryset_of_non_masters = queryset.exclude(has_slaves)

        return queryset_of_masters if value else queryset_of_non_masters


class UserOperationsHistoryFilter(rest_framework_filters.FilterSet):
    """
    Filter for UserOperationsHistoryView.
    """

    class MODEL_CHOICES(TextChoices):
        TVSERIES = archives.models.TvSeriesModel._meta.model_name
        SEASONS = archives.models.SeasonModel._meta.model_name
        IMAGES = archives.models.ImageModel._meta.model_name

    model = rest_framework_filters.MultipleChoiceFilter(
        field_name='content_type__model',
        lookup_expr='exact',
        choices=MODEL_CHOICES.choices,
    )
    as_who = rest_framework_filters.MultipleChoiceFilter(
        field_name='as_who',
        lookup_expr='exact',
        choices=administration.models.UserStatusChoices.choices,
    )
    operation_type = rest_framework_filters.MultipleChoiceFilter(
        field_name='operation_type',
        lookup_expr='exact',
        choices=administration.models.OperationTypeChoices.choices,
    )
    last_operations = rest_framework_filters.BooleanFilter(
        field_name='access_time',
        method='get_last_operations',
        label='Show last operation for chosen model(s).',
    )

    # last_operations = rest_framework_filters.NumberFilter(
    #     #field_class=forms.IntegerField,
    #     field_name='access_time',
    #     method='get_last_operations',
    #     label='Show X last operations for chosen model(s).',
    # )

    class Meta:
        model = administration.models.EntriesChangeLog
        fields = {
            'access_time': ('gte', 'lte',),
        }

    def get_last_operations(self, queryset: QuerySet, field_name: str, value: bool) -> QuerySet:
        """
        Returns last operation in chosen models.
        """
        last_operation_time = Subquery(
            self.Meta.model.objects.filter(user=OuterRef('user')).values('content_type_id').
            annotate(last_access_time=Max(field_name)).values_list('last_access_time', flat=True)
        )

        return queryset.filter(access_time__in=last_operation_time) if value else queryset

