import collections
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model, tokens
from djoser import utils
from djoser.conf import settings as djoser_settings
from rest_framework import serializers

from series import error_codes
from series.helpers.typing import User_instance


# noinspection PyProtectedMember
class UidAndTokenValidationMixin:
    """
    defines few methods to validate UID and token + extract user object from Db based on this information.
    """
    default_error_messages = {
        'invalid_token': djoser_settings.CONSTANTS.messages.INVALID_TOKEN_ERROR,
        'invalid_uid': djoser_settings.CONSTANTS.messages.INVALID_UID_ERROR,
    }

    def confirm_uid(self, uid: str) -> Optional[User_instance]:
        """
        Validates uid and if correct -tries to get user instance based on this uid.
        If user with this pk does not exists -raises Validation error.
        Returns user instance optionally.
        """
        try:
            uid = utils.decode_uid(uid)
            user = get_user_model().all_objects.get(pk=uid)
        except (get_user_model().DoesNotExist, ValueError, TypeError, OverflowError) as err:
            key_error = 'invalid_uid'
            raise serializers.ValidationError(
                {'uid': [self.default_error_messages[key_error]]}, code=key_error,
            ) from err
        else:
            return user

    def confirm_token(self, user: User_instance, token: str) -> None:
        """
        Validates users token and raises Validation error in case toke is invalid.
        /MQ/5gs-fb5ae501d135d7ddb568/ example of uid and token string
        """
        is_token_valid = tokens.default_token_generator.check_token(user, token)
        if not is_token_valid:
            key_error = 'invalid_token'
            raise serializers.ValidationError(
                     {'token': [self.default_error_messages[key_error]]}, code=key_error
                 )


class UserSlaveMutualValidationMixin:
    """
    Provides set of data validation in case of slave to user attachment.
    """
    @staticmethod
    def master_slave_mutual_data_validation(*, slave: User_instance, master: User_instance) -> None:
        """
        Validates slave to master attachment
        :param slave: User model instance of slave.
        :param master: User model instance of master.
        :return: None
        """
        errors = collections.defaultdict(list)
        codes = set()
        # Slave account cant be equal to master account.
        if master == slave:
            errors['master_email'].append(error_codes.MASTER_OF_SELF.message,)
            codes.add(error_codes.MASTER_OF_SELF.code,)
        # Master cant be slave.
        if master.is_slave:
            errors['master_email'].append(error_codes.SLAVE_CANT_HAVE_SALVES.message,)
            codes.add(error_codes.SLAVE_CANT_HAVE_SALVES.code,)
        # Check whether potential slave is available for this role.
        if not slave.is_available_slave:
            errors['slave_email'].append(error_codes.SLAVE_UNAVAILABLE.message,)
            codes.add(error_codes.SLAVE_UNAVAILABLE.code,)
        if errors:
            raise serializers.ValidationError(errors, codes,)

    @staticmethod
    def check_password(user: settings.AUTH_USER_MODEL, password: str) -> None:
        """
        Checks user's password and raises Validation error in case password is incorrect
        """
        if not user.check_password(password):
            raise serializers.ValidationError(
                {'slave_password': f'Incorrect password for slave with email - {user.email}'},
                code='invalid_password',
            )
