from rest_framework import generics, permissions
import administration.filters
import administration.serielizers


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
