from django.contrib.auth import get_user_model
from django.db.models import OuterRef, Q, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets, views

import administration.filters
import administration.models
import administration.serielizers
import archives.permissions
from series.helpers import custom_functions


class LogsListView(generics.ListAPIView):
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


class HistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Displays change history of chosen model.
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

    def get_serializer_class(self):
        if self.action == 'list':
            return administration.serielizers.HistorySerializer
        else:
            return administration.serielizers.HistoryDetailSerializer

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
                    pk__gt=OuterRef('pk'),
                ).values('state', )[:1]
            ),
            prev_state=Subquery(
                administration.models.EntriesChangeLog.objects.filter(
                    self.condition,
                    pk__lt=OuterRef('pk'),
                ).values('state', )[:1]
            ))

        obj = get_object_or_404(queryset, pk=self.kwargs['pk'])
        model_instance_to_check = getattr(self.model_instance, 'content_object', self.model_instance)
        self.check_object_permissions(self.request, model_instance_to_check)

        return obj


