from django.utils.translation import ugettext_lazy as _
from rest_framework_simplejwt import authentication, exceptions, settings, state

from series import error_codes


class SoftDeletedJWTAuthentication(authentication.JWTAuthentication):
    """
    Custom auth backend returns special message on denial for soft-deleted users.
    """
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[settings.api_settings.USER_ID_CLAIM]
        except KeyError:
            raise exceptions.InvalidToken(_('Token contained no recognizable user identification'))

        try:
            user = state.User._default_manager.get(
                **{settings.api_settings.USER_ID_FIELD: user_id}
            )
        except state.User.DoesNotExist:
            raise exceptions.AuthenticationFailed(
                _('User not found'), code='user_not_found'
            )
        if not user.is_active:
            raise exceptions.AuthenticationFailed(
                _('User is inactive'), code='user_inactive'
            )
        if user.deleted:
            raise authentication.AuthenticationFailed(
                        *error_codes.USER_IS_DELETED
                    )

        return user
