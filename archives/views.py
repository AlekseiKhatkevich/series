from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Sum
from django.db.models.functions import NullIf
from rest_framework import generics, permissions

import archives.models
import archives.serializers
from series.helpers import custom_functions
from series import pagination


class TvSeriesListCreateView(generics.ListCreateAPIView):
    pagination_class = pagination.FasterLimitOffsetPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    serializer_class = archives.serializers.TvSeriesSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        #  deferred fields for User model instance.
        user_model_deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('pk', 'first_name', 'last_name'),
            prefix='entry_author__',
        )
        #  Prefetch to show interrelationship connected series name and reason for interrelationship.
        pr_groups = Prefetch(
            'group',
            queryset=archives.models.GroupingModel.objects.all().select_related('to_series')
        )
        # Annotations for seasons and episodes.
        annotations = dict(
            seasons_cnt=NullIf(Count('seasons'), 0),
            episodes_cnt=Sum('seasons__number_of_episodes'),
        )
        self.queryset = self.model.objects.all().\
            annotate(**annotations).\
            select_related('entry_author',).\
            prefetch_related('interrelationship', 'images', pr_groups).\
            defer(*user_model_deferred_fields).order_by('pk')
        return super().get_queryset()

