from typing import Optional

import djoser.views
import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.http.request import HttpRequest
from djoser.compat import get_user_email
from djoser.conf import settings as djoser_settings
from rest_framework import exceptions, status, throttling
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt import settings as simplejwt_settings, views as simplejwt_views

import users.models
from series.helpers.typing import jwt_token


class CustomDjoserUserViewSet(djoser.views.UserViewSet):
    """
    Custom viewset based on Djoser viewset.
    """
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.prefetch_related('slaves')

    @action(['post'], detail=False)
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
        else:  # Just attach slave to master directly without confirmation from slave's part.
            serializer.save()

        return Response(status=status.HTTP_202_ACCEPTED)

    @action(['post'], detail=False)
    def undelete_account(self, request, *args, **kwargs):
        """
        Action for undelete soft-deleted user account.
        """
        self.get_object = ???
        pass

    def get_permissions(self):
        if self.action == 'set_slaves':
            self.permission_classes = djoser_settings.PERMISSIONS.set_slaves
        elif self.action == 'undelete_account':
            return djoser_settings.PERMISSIONS.undelete_account
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'set_slaves':
            return djoser_settings.SERIALIZERS.set_slaves
        elif self.action == 'undelete_account':
            return djoser_settings.SERIALIZERS.undelete_account
        return super().get_serializer_class()

    def permission_denied(self, request, message=None):
        if self.action == 'resend_activation':
            raise exceptions.PermissionDenied(detail=message)
        super().permission_denied(request, message=message)

    def get_throttles(self):
        for act in self.get_extra_actions():
            if act.__name__ in settings.REST_FRAMEWORK.get('DEFAULT_THROTTLE_RATES', ()):
                setattr(self, 'throttle_scope', act.__name__)
        return super().get_throttles()


class CustomJWTTokenRefreshView(simplejwt_views.TokenRefreshView):
    """
    Subclass of simple-JWT token refresh view in order to add functionality for
    writing user's ip address before new access token is rendered.
    """

    @staticmethod
    def write_user_ip(request: HttpRequest, token: jwt_token) -> Optional[users.models.UserIP]:
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
