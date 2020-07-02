from django.contrib.auth import get_user_model
from django.db.models import Exists, OuterRef, QuerySet
from django_filters import rest_framework as rest_framework_filters


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
