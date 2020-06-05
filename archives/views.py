from django.contrib.auth import get_user_model
from rest_framework import generics, permissions
from django.db.models import Prefetch
import archives.models
import archives.serializers
from series.helpers import custom_functions


class TvSeriesListCreateView(generics.ListCreateAPIView):
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    serializer_class = archives.serializers.TvSeriesSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user_model_deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('pk', 'first_name', 'last_name'),
            prefix='entry_author__',
        )
        self.queryset = self.model.objects.all().\
            select_related('entry_author').\
            prefetch_related('interrelationship', 'group').\
            defer(*user_model_deferred_fields)
        return super().get_queryset()

