import os
import tempfile

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import decorators, generics, permissions, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_extensions.cache.mixins import ListCacheResponseMixin
from rest_framework_extensions.mixins import DetailSerializerMixin

import administration.filters
import administration.models
import administration.serielizers
import archives.permissions
from administration import cache_functions, key_constructors
from series.helpers import custom_functions


class LogsListView(ListCacheResponseMixin, generics.ListAPIView):
    """
    View to show logs.
    """
    serializer_class = administration.serielizers.LogsSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()
    permission_classes = (permissions.IsAdminUser,)
    filterset_class = administration.filters.LogsFilterSet
    ordering = ('-create_datetime',)
    ordering_fields = (
        'level',
        'create_datetime',
    )
    search_fields = (
        'msg',
        'trace',
    )
    list_cache_key_func = key_constructors.LogsListViewKeyConstructor()
    list_cache_timeout = 60*60


class HistoryViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    """
    Displays change history of chosen model entry.
    """
    permission_classes = (
        permissions.IsAuthenticated,
        archives.permissions.MasterSlaveRelations |
        archives.permissions.FriendsGuardianPermission |
        archives.permissions.HandleDeletedUsersEntriesPermission,
    )
    filterset_class = administration.filters.HistoryViewSetFilterSet
    ordering = ('-access_time',)
    ordering_fields = ('access_time', 'user',)
    search_fields = ('user',)
    serializer_class = administration.serielizers.HistorySerializer
    serializer_detail_class = administration.serielizers.HistoryDetailSerializer

    def get_queryset(self):
        model = self.kwargs['model_name']
        instance_pk = self.kwargs['instance_pk']

        self.condition = Q(
            object_id=instance_pk,
            content_type__model=model.__name__.lower(),
            content_type__app_label=model._meta.app_label.lower(),
        )

        deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            prefix='user__',
            fields_to_remove=('email',),
        )
        if self.action == 'list':
            deferred_fields.add('state')

        self.queryset = administration.models.EntriesChangeLog.objects.filter(self.condition). \
            select_related('user', ).defer(*deferred_fields)

        return super().get_queryset()

    def dispatch(self, request, *args, **kwargs):
        """
        Here we check whether or not object with pk and models from url kwargs exists in fact.
        """
        model_instance = get_object_or_404(
            self.kwargs['model_name'],
            pk=self.kwargs['instance_pk'],
        )
        setattr(self, 'model_instance', model_instance)

        return super().dispatch(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """
        Enforce permissions check here as by default list action does not do it.
        """
        #  Pass series related to image in case object is image, as image doesn't have entry_author.
        model_instance_to_check = getattr(self.model_instance, 'content_object', self.model_instance)
        self.check_object_permissions(self.request, model_instance_to_check)

        return super().list(request, *args, **kwargs)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())

        queryset = queryset.annotate(
            next_state=Subquery(
                administration.models.EntriesChangeLog.objects.filter(
                    self.condition,
                    access_time__gt=OuterRef('access_time'),
                ).order_by('access_time').values('state', )[:1]
            ),
            prev_state=Subquery(
                administration.models.EntriesChangeLog.objects.filter(
                    self.condition,
                    access_time__lt=OuterRef('access_time'),
                ).order_by('-access_time').values('state', )[:1]
            ))

        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        model_instance_to_check = getattr(self.model_instance, 'content_object', self.model_instance)
        self.check_object_permissions(self.request, model_instance_to_check)

        return obj


@decorators.api_view(http_method_names=['GET'])
@decorators.permission_classes([permissions.IsAdminUser, ])
def coverage_view(request: Request) -> Response:
    """
    Views to show .coverage test results.
    """
    data_key = 'coverage_data_key'
    time_key = 'coverage_time_key'

    cached_data = cache.get_many((data_key, time_key, ))
    json_report = cached_data.get(data_key, None)
    stored_time = cached_data.get(time_key, None)

    coverage_last_time_ran = cache_functions.get_coverage_last_time()
    assert coverage_last_time_ran is not None, 'Coverage has not ran yet.'

    # If not data sored in cache or stored data is old...
    if None in (json_report, stored_time) or coverage_last_time_ran > stored_time:

        file = tempfile.NamedTemporaryFile(delete=False)

        try:
            os.system(f'coverage json -o {file.name}')
            file.seek(os.SEEK_SET)
            json_report = file.read()
            cache.set_many({
                    data_key: json_report,
                    time_key: coverage_last_time_ran
                })
        finally:
            file.close()
            os.remove(file.name)

    return Response(data=json_report)

