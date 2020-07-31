from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, viewsets

import administration.filters
import administration.serielizers
import archives.permissions
import archives.models
from series.helpers import custom_functions


class LogsListView(generics.ListAPIView):
    """
    View to show logs.
    """
    serializer_class = administration.serielizers.LogsSerializer
    model = serializer_class.Meta.model
    queryset = model.objects.all()
    permission_classes = (permissions.IsAdminUser, )
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
    serializer_class = administration.serielizers.HistorySerializer
    model = serializer_class.Meta.model
    permission_classes = (
        permissions.IsAuthenticated,
        archives.permissions.MasterSlaveRelations |
        archives.permissions.FriendsGuardianPermission |
        archives.permissions.HandleDeletedUsersEntriesPermission,
    )

    def get_queryset(self):
        model = self.kwargs['model_name']
        instance_pk = self.kwargs['instance_pk']

        deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            prefix='user__',
            fields_to_remove=('email', ),
        )
        if self.action == 'list':
            deferred_fields.add('state')

        self.queryset = self.model.objects.filter(
            object_id=instance_pk,
            content_type__model=model.__name__.lower(),
            content_type__app_label=model._meta.app_label.lower(),
        ).select_related('user', ).defer(*deferred_fields)

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





