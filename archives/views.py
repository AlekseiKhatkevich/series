import functools
from typing import Sequence, Tuple

import guardian.models
from django.contrib.auth import get_user_model
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchHeadline
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count, F, Prefetch, Q, Subquery, Sum, base, functions, Window
from django.db.utils import ProgrammingError
from django.shortcuts import get_object_or_404
from rest_framework import decorators, exceptions, generics, mixins, parsers, permissions, \
    status, viewsets
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework_extensions.mixins import DetailSerializerMixin
import archives.filters
import archives.models
import archives.permissions
import archives.serializers
from archives.helpers import language_codes
from series import constants, error_codes, pagination
from series.helpers import custom_functions, view_mixins


class TvSeriesBase(generics.GenericAPIView):
    """
    Base view class for TV series views.
    """

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
            seasons_cnt=functions.NullIf(Count('seasons'), 0),
            episodes_cnt=Sum('seasons__number_of_episodes'),
        )
        self.queryset = self.model.objects.all(). \
            annotate(**annotations). \
            select_related('entry_author', ). \
            prefetch_related('images', pr_groups, ). \
            defer(*user_model_deferred_fields)

        return super().get_queryset()

    @functools.lru_cache(maxsize=1)
    def get_object(self):
        return super().get_object()


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
            queryset=archives.models.SeasonModel.objects.all().only('pk', 'season_number', 'series_id', )
        )
        return qs.select_related('entry_author__master', ).prefetch_related(pr_seasons, )


class TvSeriesListCreateView(generics.ListCreateAPIView, TvSeriesBase):
    pagination_class = pagination.FasterLimitOffsetPagination
    serializer_class = archives.serializers.TvSeriesSerializer
    filterset_class = archives.filters.TvSeriesListCreateViewFilter
    ordering = ('pk',)
    ordering_fields = (
        'name',
        'rating',
        'translation_years',
        'entry_author__last_name',
    )
    search_fields = ('name',)


class FileUploadDeleteView(mixins.DestroyModelMixin, generics.CreateAPIView):
    """
    Api for uploading and deleting images for TvSeries.
    Filename should be with extension, for example 'picture.jpg'.
    """
    parser_classes = (parsers.FileUploadParser,)
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
        self.queryset = archives.models.TvSeriesModel.objects.all(). \
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
            status=status.HTTP_204_NO_CONTENT,
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
        exists_in_db = series.images.filter(pk__in=self.kwargs['image_pk']). \
            values_list('pk', flat=True)
        wrong_image_pks = set(images_pks).difference(exists_in_db)

        if wrong_image_pks:
            raise exceptions.ValidationError(
                f'Images with pk {" ,".join(map(str, wrong_image_pks))} does not exist in the database.'
            )


class SeasonsViewSet(
    view_mixins.ViewSetActionPermissionMixin,
    DetailSerializerMixin,
    viewsets.ModelViewSet,
):
    """
    ViewSet for SeasonModel.
    """
    serializer_class = archives.serializers.SeasonsSerializer
    serializer_detail_class = archives.serializers.DetailSeasonSerializer
    model = serializer_class.Meta.model
    filterset_class = archives.filters.SeasonsFilterSet
    ordering = ('_order',)
    ordering_fields = (
        'season_number',
        'number_of_episodes',
    )
    non_safe_methods_permissions = (
        permissions.IsAuthenticated,
        archives.permissions.MasterSlaveRelations |
        archives.permissions.FriendsGuardianPermission |
        archives.permissions.HandleDeletedUsersEntriesPermission,
    )
    permission_action_classes = dict.fromkeys(
        (
            'create',
            'destroy',
            'update',
            'partial_update',
            'add_subtitle',
            'delete_subtitle',
        ),
        non_safe_methods_permissions,
    )

    def create(self, request, *args, **kwargs):
        """
        We call check_object_permissions() here in order to validate permissions of
        current user to root series object.
        """
        self.check_object_permissions(self.request, self.series)

        return super().create(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        """
        Here we check whether or not series with given 'series_pk' url kwarg exists.
        """
        series = get_object_or_404(
            archives.models.TvSeriesModel,
            pk=self.kwargs['series_pk'],
        )
        setattr(self, 'series', series)

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user_model_deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('pk', 'first_name', 'last_name', 'deleted', 'deleted_time',),
            prefix='entry_author__',
        )

        series_pk = self.kwargs['series_pk']
        self.queryset = self.model.objects.filter(series_id=series_pk). \
            select_related('entry_author', ).defer(*user_model_deferred_fields)

        return super().get_queryset()

    @functools.lru_cache(maxsize=1)
    def get_object(self):
        return super().get_object()

    @decorators.action(detail=True, methods=['post'], )
    def add_subtitle(self, request, *args, **kwargs):
        """
        Creates subtitle entry in DB connected with current season.
        """
        serializer = archives.serializers.SubtitlesUploadSerializer(
            data=request.data,
            context={'season': self.get_object()},
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()

        return Response(status=status.HTTP_201_CREATED)

    @decorators.action(
        detail=True,
        methods=['delete'],
        url_path=r'delete_subtitle/(?P<subtitle_id>\d+)',
    )
    def delete_subtitle(self, request, *args, **kwargs):
        """
        Deletes one subtitle entry.
        """
        deleted, _ = self.get_object().subtitle.filter(pk=kwargs['subtitle_id']).delete()
        if not deleted:
            raise exceptions.ValidationError(
                *error_codes.NO_SUCH_SUBTITLE
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserObjectPermissionView(mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               mixins.ListModelMixin,
                               viewsets.GenericViewSet, ):
    """
    View to create and delete  and view object permissions on certain objects for another user.
    """
    serializer_class = archives.serializers.ManagePermissionsSerializer
    perm_model = serializer_class.Meta.model
    permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE
    pagination_class = pagination.FasterLimitOffsetPagination
    filterset_class = archives.filters.UserObjectPermissionFilterSet
    ordering = ('content_type__model',)
    ordering_fields = (
        'pk',
        'user__email',
        'content_type__model',
        'object_pk',
    )
    search_fields = (
        '^user__last_name',
        '^user__first_name',
        '^user__email',
    )

    def get_condition(self, model: base.ModelBase) -> Q:
        """
        Returns Q condition with list of user entries pks in provided model.
        """
        entries_pks = Subquery(model.objects.filter(entry_author=self.request.user).values('pk'))
        condition = Q(
            object_pk__int__in=entries_pks,
            content_type__model=model._meta.model_name,
            content_type__app_label=model._meta.app_label,
        )

        return condition

    def get_queryset(self):
        user_model_deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            fields_to_remove=('pk', 'email',),
            prefix='user__',
        )

        self.queryset = self.perm_model.objects.filter(
            self.get_condition(archives.models.TvSeriesModel) |
            self.get_condition(archives.models.SeasonModel) |
            self.get_condition(archives.models.ImageModel),
            permission__codename=self.permission_code,
        ).select_related('user', 'content_type', ).defer(
            *user_model_deferred_fields,
            'content_type__app_label',
            'content_type__id',
        )

        return super().get_queryset()


class FTSListViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    """
    View displays list of series where key word(s) or key phrase(s) is(are) present.
    """
    serializer_class = archives.serializers.FTSSerializer
    serializer_detail_class = archives.serializers.FTSDetailSerializer
    model = serializer_class.Meta.model
    default_search_configuration = 'simple'

    def validate_query_params(self) -> Tuple[str, str, str]:
        """
        Validates query parameters.
        """
        errors = list()
        allowed_search_types = SearchQuery.SEARCH_TYPES

        try:
            search = self.request.query_params['search']
        except KeyError:
            errors.append(error_codes.NO_SEARCH.message)

        language_code = self.request.query_params.get('language', None)
        if language_code is not None and language_code not in language_codes.codes_iterator:
            errors.append(error_codes.WRONG_LANGUAGE_CODE.message)

        search_type = self.request.query_params.get('search_type', 'plain')
        if search_type not in allowed_search_types:
            errors.append(error_codes.WRONG_SEARCH_TYPE.message)

        if errors:
            raise exceptions.ValidationError(
                {'query_parameters': errors},
                code='query_params_errors',
            )
        # noinspection PyUnboundLocalVariable
        return search, language_code, search_type

    def get_queryset(self):
        search, language_code, search_type = self.validate_query_params()
        search_query = SearchQuery(
            search,
            config=F('search_configuration'),
            search_type=search_type,
        )
        fts_condition = Q(full_text=F('search_query'))
        language_condition = Q(language=language_code)
        condition = fts_condition & language_condition if language_code is not None else fts_condition
        subtitles_deferred_fields_fields = (
            'text',
            'full_text',
            'search_configuration',
        )
        season_deferred_fields = custom_functions.get_model_fields_subset(
            model=archives.models.SeasonModel,
            prefix='season__',
            fields_to_remove=(
                'series',
                'season_number',
            ), )
        search_rank = SearchRank(
            F('full_text'),
            search_query,
            cover_density=True,
            normalization=32,
        )
        # Rank like 1,2,3 instead of 0.9, 0.76, 0.044, etc
        positional_rank = Window(
            expression=functions.RowNumber(),
            order_by=search_rank.desc(),
        )

        self.queryset = self.model.objects.annotate(
            search_query=search_query,
            positional_rank=positional_rank,
        ).filter(
            condition,
        ).select_related(
            'season',
            'season__series',
        ).defer(
            *subtitles_deferred_fields_fields,
            *season_deferred_fields,
        ).order_by(
            'positional_rank',
        )

        return super().get_queryset()

    @property
    def queryset_detail(self):
        search, language_code, search_type = self.validate_query_params()
        search_query = SearchQuery(
            search,
            config=F('search_configuration'),
            search_type=search_type,
        )
        subtitles_deferred_fields = custom_functions.get_model_fields_subset(
            model=archives.models.Subtitles,
            fields_to_remove=('id',)
        )
        self.queryset = self.model.objects.annotate(
            headline=SearchHeadline(
                expression=F('text'),
                query=search_query,
                config=F('search_configuration'),
                max_words=25,
                min_words=15,
                short_word=3,
                max_fragments=10,
            )).defer(*subtitles_deferred_fields)

        return self.queryset

    def paginate_queryset(self, queryset):
        """
        We validate here 'raw fts search' formatting.
        """
        try:
            return super().paginate_queryset(queryset)
        except ProgrammingError as err:
            raise exceptions.ValidationError(
                {'query_parameters': error_codes.WRONG_RAW_SEARCH.message},
                code=error_codes.WRONG_RAW_SEARCH.code,
            ) from err
