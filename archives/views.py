from typing import Sequence

import guardian.models
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count, Prefetch, Sum
from django.db.models.functions import NullIf
from rest_framework import exceptions, generics, mixins, parsers, permissions, status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response

import archives.filters
import archives.models
import archives.permissions
import archives.serializers
from series import error_codes, pagination
from series.helpers import custom_functions


class TvSeriesBase(generics.GenericAPIView):
    """
    Base view class for TV series views.
    """
    _obj = None

    @property
    def model(self):
        return getattr(self.serializer_class.Meta, 'model')

    def get_queryset(self):
        #  deferred fields for User model instance.
        user_model_deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('pk', 'first_name', 'last_name', 'master'),
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
            select_related('entry_author', ).\
            prefetch_related('images', pr_groups, ).\
            defer(*user_model_deferred_fields)
        return super().get_queryset()

    def get_object(self):
        # To use saved in instance 'obj' object instead of calling function each ad every time.
        if self._obj is None:
            self._obj = super().get_object()
        return self._obj


class TvSeriesDetailView(generics.RetrieveUpdateDestroyAPIView, TvSeriesBase):
    permission_classes = [
        archives.permissions.ReadOnlyIfOnlyAuthenticated |
        archives.permissions.MasterSlaveRelations |
        archives.permissions.FriendsGuardianPermission
    ]
    lookup_url_kwarg = 'series_pk'
    serializer_class = archives.serializers.TvSeriesDetailSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pr_seasons = Prefetch(
            'seasons',
            queryset=archives.models.SeasonModel.objects.all().only('pk', 'season_number', 'series_id',)
        )
        return qs.select_related('entry_author__master', ).prefetch_related(pr_seasons, )


class TvSeriesListCreateView(generics.ListCreateAPIView, TvSeriesBase):
    pagination_class = pagination.FasterLimitOffsetPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly, )
    serializer_class = archives.serializers.TvSeriesSerializer
    filterset_class = archives.filters.TvSeriesListCreateViewFilter
    ordering = ('pk', )
    ordering_fields = (
        'name',
        'rating',
        'translation_years',
        'entry_author__last_name',
    )
    search_fields = ('name', )


class FileUploadDeleteView(mixins.DestroyModelMixin, generics.CreateAPIView):
    """
    Api for uploading and deleting images for TvSeries.
    Filename should be with extension, for example 'picture.jpg'.
    """
    parser_classes = (parsers.FileUploadParser, )
    permission_classes = (
            archives.permissions.MasterSlaveRelations |
            archives.permissions.FriendsGuardianPermission,
    )
    serializer_class = archives.serializers.ImagesSerializer
    lookup_url_kwarg = 'series_pk'
    model = serializer_class.Meta.model

    def get_queryset(self):
        pr_permissions = Prefetch(
            'entry_author__userobjectpermission_set',
            queryset=guardian.models.UserObjectPermission.objects.filter(
                user=self.request.user,
                object_pk=self.kwargs['series_pk'],
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ))
        self.queryset = archives.models.TvSeriesModel.objects.all().\
            select_related('entry_author').prefetch_related(pr_permissions)
        return super().get_queryset()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['series'] = self.get_object()
        return context

    def get_file(self, request: Request) -> ContentFile:
        """
        Fetches file stream from request and transforms it into actual file object.
        """
        try:
            in_memory_uploaded_file = request.data['file']
            assert isinstance(in_memory_uploaded_file, UploadedFile)
        except (KeyError, AssertionError) as err:
            raise exceptions.ValidationError(*error_codes.NOT_A_BINARY) from err

        try:
            image_file = ContentFile(
                in_memory_uploaded_file.read(),
                name=self.kwargs['filename']
            )
        finally:
            in_memory_uploaded_file.close()
        return image_file

    def create(self, request, *args, **kwargs):
        request.data['image'] = self.get_file(request)
        return super().create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        images_pks = self.kwargs['image_pk']
        series = self.get_object()
        self.validate_images_to_delete(series, images_pks)
        deleted_amount, _ = series.images.filter(pk__in=images_pks).delete()
        #  Delete image_hash stored in view class.
        for pk in images_pks:
            self.model.delete_stored_image_hash(pk)

        return Response(
            data={'Number_of_deleted_images': deleted_amount},
            status=status.HTTP_204_NO_CONTENT
        )

    def validate_images_to_delete(
            self,
            series: archives.models.TvSeriesModel,
            images_pks: Sequence[int],
    ) -> None:
        """
        Validates whether images with a given pks exist in database. raises exception if at least
        one of the images pks does not exist in the database.
        """
        exists_in_db = series.images.filter(
            pk__in=self.kwargs['image_pk']).values_list('pk', flat=True
                                                        )
        wrong_image_pks = set(images_pks).difference(exists_in_db)
        if wrong_image_pks:
            raise exceptions.ValidationError(
                f'Images with pk {" ,".join(map(str, wrong_image_pks))} does not exist in the database.'
            )


class SeasonsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SeasonModel.
    """
    queryset = archives.models.SeasonModel.objects.all()





