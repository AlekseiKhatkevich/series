from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Count, Prefetch, Sum
from django.db.models.functions import NullIf
from rest_framework import exceptions, generics, mixins, parsers, permissions, status
from rest_framework.response import Response
from rest_framework.request import Request

import archives.models
import archives.permissions
import archives.serializers
from series import error_codes, pagination
from series.helpers import custom_functions


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
            prefetch_related('images', pr_groups).\
            defer(*user_model_deferred_fields).order_by('pk')
        return super().get_queryset()


class FileUploadDeleteView(mixins.DestroyModelMixin, generics.CreateAPIView):
    """
    Api for uploading and deleting images for TvSeries.
    Filename should be with extension, for example 'picture.jpg'.
    """
    parser_classes = (parsers.FileUploadParser, )
    permission_classes = (archives.permissions.MasterSlaveRelations, )
    serializer_class = archives.serializers.ImagesSerializer
    queryset = archives.models.TvSeriesModel.objects.all().select_related('entry_author')
    lookup_url_kwarg = 'series_pk'

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
            assert isinstance(in_memory_uploaded_file, InMemoryUploadedFile)
        except (KeyError, AssertionError) as err:
            raise exceptions.ValidationError(*error_codes.NOT_A_BINARY) from err

        image_file = ContentFile(
            in_memory_uploaded_file.read(),
            name=self.kwargs['filename']
        )
        image_file.close()
        return image_file

    def create(self, request, *args, **kwargs):
        request.data['image'] = self.get_file(request)
        return super().create(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        series = self.get_object()
        self.validate_images_to_delete(series)
        deleted_amount, _ = series.images.filter(pk__in=self.kwargs['image_pk']).delete()

        return Response(
            data={'Number_of_deleted_images': deleted_amount},
            status=status.HTTP_204_NO_CONTENT
        )

    def validate_images_to_delete(self, series: archives.models.TvSeriesModel) -> None:
        """
        Validates whether images with a given pks exist in database. raises exception if at least
        one of the images pks does not exist in the database.
        """
        exists_in_db = series.images.filter(
            pk__in=self.kwargs['image_pk']).values_list('pk', flat=True
                                                        )
        wrong_image_pks = set(self.kwargs['image_pk']).difference(exists_in_db)
        if wrong_image_pks:
            raise exceptions.ValidationError(
                f'Images with pk {" ,".join(map(str, wrong_image_pks))} does not exist in the database.'
            )





