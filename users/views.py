from typing import Optional, Type

import djoser.views
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from django.utils.functional import cached_property
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from rest_framework import exceptions, status, throttling
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework_simplejwt import settings as simplejwt_settings, views as simplejwt_views

import users.filters
import users.models
from series import error_codes
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
        if self.action in ('resend_activation', ):
            raise exceptions.PermissionDenied(detail=message)
        super().permission_denied(request, message=message)

    def get_throttles(self):
        if self.action in getattr(api_settings, 'DEFAULT_THROTTLE_RATES', ()):
            setattr(self, 'throttle_scope', self.action)
        return super().get_throttles()


class CustomJWTTokenRefreshView(simplejwt_views.TokenRefreshView):
    """
    Subclass of simple-JWT token refresh view in order to add functionality for
    writing user's ip address before new access token is rendered.
    """

    def write_user_ip(self, request: HttpRequest, token: jwt_token) -> Optional[users.models.UserIP]:
        """
        Method extracts user_id from JWT token, gets user ip address from request
        and writes 'UserIP' models entry in DB successfully saving user's ip in DB.
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


class UserLastEntries(simplejwt_views.generics.RetrieveAPIView):
    """
    Displays user's last entries in each category.
    """
    # EntriesChangeLog.objects.filter(user_id=1).values('content_type_id').\
    #     annotate(time=Max('access_time')).values_list(
    #     'time', flat=True)