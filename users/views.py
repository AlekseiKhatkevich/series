from typing import Optional, Type

import djoser.views
import guardian.models
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.db.models import F, IntegerField, Prefetch, Q, QuerySet, Subquery, Value, Window, functions
from django.db.models.base import ModelBase
from django.http.request import HttpRequest
from django.utils.functional import cached_property
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from rest_framework import exceptions, status, throttling, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt import settings as simplejwt_settings, views as simplejwt_views

import administration.serielizers
import archives.models
import users.database_functions
import users.filters
import users.models
import users.serializers
from series import constants, error_codes, pagination
from series.helpers import custom_functions
from series.helpers.typing import jwt_token
from users.helpers import views_mixins


class CustomDjoserUserViewSet(djoser.views.UserViewSet):
    """
    Custom viewset based on Djoser viewset.
    """
    filterset_class = users.filters.UsersListFilter
    ordering = ('last_name',)
    ordering_fields = (
        'email',
        'last_login',
        'date_joined',
        'last_name',
        'first_name',
        'user_country',
    )
    search_fields = (
        '^email', '=email',
        '^first_name', '=first_name',
        '^last_name', '=last_name',
    )

    def get_queryset(self):
        """
        Fetch slave PKs for list action.
        """
        qs = super().get_queryset()
        if self.action == 'list':
            qs = qs.annotate(slv=ArrayAgg('slaves', distinct=True))
        return qs

    @cached_property
    def get_child_extra_actions(self):
        """
        Returns only extra actions defined in this exact viewset exclude actions defined in superclasses.
        """
        cls = self.__class__
        all_extra_actions = cls.get_extra_actions()
        parent_extra_actions = cls.__base__.get_extra_actions()
        child_extra_actions = set(all_extra_actions).difference(parent_extra_actions)
        return (act.__name__ for act in child_extra_actions)

    @action(['post'], detail=False, permission_classes=djoser_settings.PERMISSIONS.master_slave_interchange)
    def master_slave_interchange(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            pass
        else:
            serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @action(['post'], detail=False, permission_classes=djoser_settings.PERMISSIONS.set_slaves)
    def set_slaves(self, request, *args, **kwargs):
        """
        Action for attaching slave account to a master account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Send activation email to slave.
        if djoser_settings.SEND_ACTIVATION_EMAIL:
            slave = serializer.slave
            context = {'slave': slave, 'master': request.user}
            to = [get_user_email(slave)]
            djoser_settings.EMAIL.slave_activation(self.request, context).send(to)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:  # Just attach slave to master directly without confirmation from slave's part.
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

    @action(['post'], detail=False, permission_classes=djoser_settings.PERMISSIONS.confirm_set_slaves)
    def confirm_set_slaves(self, request, *args, **kwargs):
        """
        Action confirms 2 pcs. uid and token received from FE and attaches slave to master.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if djoser_settings.SEND_CONFIRMATION_EMAIL:
            slave, master = serializer.slave, serializer.master
            for person in (master, slave):
                context = {'user': person}
                to = [get_user_email(person)]
                djoser_settings.EMAIL.confirmation(self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(['post'], detail=False, permission_classes=djoser_settings.PERMISSIONS.undelete_account)
    def undelete_account(self, request, *args, **kwargs):
        """
        Action for undelete soft-deleted user account.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if djoser_settings.SEND_ACTIVATION_EMAIL:
            soft_deleted_user = serializer.soft_deleted_user
            context = {'soft_deleted_user': soft_deleted_user}
            to = [get_user_email(soft_deleted_user)]
            djoser_settings.EMAIL.undelete_account(self.request, context).send(to)
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)

    @action(['post'], detail=False, permission_classes=djoser_settings.PERMISSIONS.confirm_undelete_account)
    def confirm_undelete_account(self, request, *args, **kwargs):
        """
        Action to confirm account restoration by email link.
        /MQ/5gs-fb5ae501d135d7ddb568/ example of uid and token string
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.user
        user.deleted = False
        user.save()

        if djoser_settings.SEND_CONFIRMATION_EMAIL:
            context = {'user': user}
            to = [get_user_email(user)]
            djoser_settings.EMAIL.confirmation(self.request, context).send(to)

        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action in self.get_child_extra_actions:
            return getattr(djoser_settings.SERIALIZERS, self.action)
        return super().get_serializer_class()

    def permission_denied(self, request, message=None):
        if self.action in ('resend_activation',):
            raise exceptions.PermissionDenied(detail=message)
        super().permission_denied(request, message=message)

    def get_throttles(self):
        if self.action in getattr(api_settings, 'DEFAULT_THROTTLE_RATES', ()):
            setattr(self, 'throttle_scope', self.action)
        return super().get_throttles()


class CustomJWTTokenRefreshView(simplejwt_views.TokenRefreshView):
    """
    Subclass of simple-JWT token refresh view in order to add functionality for
    writing user'sip address before new access token is rendered.
    """

    def write_user_ip(self, request: HttpRequest, token: jwt_token) -> Optional[users.models.UserIP]:
        """
        Method extracts user_id from JWT token, gets userip address from request
        and writes 'UserIP' models entry in DB successfully saving user'sip in DB.
        Returns None if something went wong.
        """
        if token is not None:
            key = settings.SIMPLE_JWT.get(
                'SIGNING_KEY',
                settings.SECRET_KEY
            )
            algorithm = settings.SIMPLE_JWT.get(
                'ALGORITHM',
                simplejwt_settings.DEFAULTS['ALGORITHM']
            )
            decoded = jwt.decode(
                jwt=token,
                key=key,
                algorithms=[algorithm, ]
            )
            user_id = decoded['user_id']
            user_ip_address = throttling.BaseThrottle().get_ident(request)

            self.filter_soft_deleted_users(user_id=user_id)

            try:
                return users.models.UserIP.objects.create(
                    user_id=user_id,
                    ip=user_ip_address,
                )
            except (ValidationError, get_user_model().DoesNotExist,):
                return None

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = response.data.get('access', None)
        self.write_user_ip(request, token)
        return response

    @staticmethod
    def filter_soft_deleted_users(user_id: Type[int]) -> None:
        """
        Raises validation error if user with given pk is soft-deleted.
        """
        if get_user_model().objects.is_soft_deleted(pk=user_id):
            raise ValidationError(
                {'email': error_codes.SOFT_DELETED_DENIED.message},
                code=error_codes.SOFT_DELETED_DENIED.code,
            )


class CustomTokenObtainPairView(views_mixins.TokenViewBaseMixin, simplejwt_views.TokenObtainPairView):
    """
    Difference to standard 'TokenObtainPairView' is that in case user is soft-deleted, view would
    raise exception.
    """
    pass


class UserEntries(simplejwt_views.generics.RetrieveAPIView):
    """
    Displays user's entries in each category.
    """
    serializer_class = users.serializers.UserEntriesSerializer
    model = serializer_class.Meta.model

    def get_queryset(self):
        user = self.request.user
        pr_seasons = Prefetch(
            'seasons',
            queryset=user.seasons.all().select_related('series', ),
        )
        pr_images = Prefetch(
            'images',
            queryset=user.images.all().prefetch_related('content_object', ),
        )
        self.queryset = get_user_model().objects.filter(pk=user.pk).prefetch_related(
            'series',
            pr_seasons,
            pr_images,
        )
        return super().get_queryset()

    def get_object(self):
        return self.get_queryset().first()


class AllowedToHandleEntries(views.APIView):
    """
    Displays entries that are allowed to be managed by request user.
    1) User is master, or
    2) User is slave, or
    3) User has object permission.
    """
    serializer_class = users.serializers.UserEntriesSerializer
    permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE

    def get_individual_queryset(self, model: ModelBase) -> QuerySet:
        """
        Returns individual queryset on a given model with object that are allowed to be handled
        by request user.
        """
        user = self.request.user
        slaves = Subquery(get_user_model().objects.filter(master=user).values('pk'))
        master_id = user.master_id

        friend_objects_pks = Subquery(
            guardian.models.UserObjectPermission.objects.filter(
                content_type__model=model._meta.model_name,
                content_type__app_label=model._meta.app_label,
                user=user,
                permission__codename=self.permission_code,
            ).values(object_pk_int=functions.Cast(F('object_pk'), output_field=IntegerField()))
        )

        qs = model.objects.filter(
            Q(entry_author_id=master_id) |
            Q(entry_author_id__in=slaves) |
            Q(pk__in=friend_objects_pks),
        )

        if model == archives.models.SeasonModel:
            qs = qs.select_related('series', )
        elif model == archives.models.ImageModel:
            qs = qs.prefetch_related('content_object', )

        return qs

    def get(self, request, format=None):
        obj = QuerySet()
        obj.series = self.get_individual_queryset(archives.models.TvSeriesModel)
        obj.seasons = self.get_individual_queryset(archives.models.SeasonModel)
        obj.images = self.get_individual_queryset(archives.models.ImageModel)
        serializer = self.serializer_class(obj)

        return Response(serializer.data)


class UserOperationsHistoryView(simplejwt_views.generics.ListAPIView):
    """
    Displays history of user's operations.
    """
    serializer_class = administration.serielizers.UserHistorySerializer
    model = serializer_class.Meta.model
    pagination_class = pagination.FasterLimitOffsetPagination
    filterset_class = users.filters.UserOperationsHistoryFilter
    ordering = ('-access_time',)
    ordering_fields = (
        'content_type__model',
        'operation_type',
        'as_who',
        'access_time',
    )

    def get_queryset(self):
        prev_val = Window(
            expression=functions.Lag('state'),
            partition_by=('content_type_id', 'object_id'),
            order_by=F('access_time').asc(),
        )
        self.queryset = self.model.objects.filter(user=self.request.user). \
            select_related('content_type').annotate(
            diff=users.database_functions.JSONDiff(prev_val, 'state')
        )
        return super().get_queryset()


class UserOwnedObjectsOperationsHistoryView(UserOperationsHistoryView):
    """
    Displays list of operations being maid on objects that are owned by request user.
    """
    serializer_class = administration.serielizers.UserOwnedObjectsOperationsHistorySerializer
    ordering_fields = UserOperationsHistoryView.ordering_fields + ('user',)
    search_fields = (
        '@full_name',
    )

    def get_queryset(self):
        deferred_fields = custom_functions.get_model_fields_subset(
            model=get_user_model(),
            prefix='user__',
            fields_to_remove=('pk', 'first_name', 'last_name',),
        )
        qs = super().get_queryset()
        custom_functions.remove_filter('user', qs)
        qs = qs.filter(
            Q(series__entry_author=self.request.user) |
            Q(seasons__entry_author=self.request.user) |
            Q(images__entry_author=self.request.user),
        ).annotate(
            full_name=functions.Concat('user__first_name', Value(' '), 'user__last_name', )
        ).select_related('user', ).defer(*deferred_fields)
        return qs


