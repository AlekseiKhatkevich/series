from types import MappingProxyType
from typing import Optional

from django.contrib.auth import get_user_model, tokens
from djoser import utils
from djoser.conf import settings as djoser_settings
from rest_framework import serializers

from series import error_codes
from series.helpers.typing import User_instance


class ConditionalRequiredPerFieldMixin:
    """
    Allows to use serializer methods to allow change field is required or not.
    To do so you need to use method 'is_{field_name}_required' which should return bool.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            method_name = f'is_{field_name}_required'
            if hasattr(self, method_name):
                field.required = getattr(self, method_name)()


#  https://stackoverflow.com/questions/48009349/django-rest-framework-conditionally-required-fields
class ActionRequiredFieldsMixin:
    """Required fields per DRF action
    Example:
    PER_ACTION_REQUIRED_FIELDS = {
        'update': ['notes']
    }
    """
    PER_ACTION_REQUIRED_FIELDS = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('view'):
            action = self.context['view'].action
            required_fields = (self.PER_ACTION_REQUIRED_FIELDS or {}).get(action)
            if required_fields:
                for field_name in required_fields:
                    self.fields[field_name].required = True


class RequiredTogetherFieldsMixin:
    """
    Allow to specify few fields as required together. They are not required until at leas one field from
    this set is filled with data. That would trigger all other fields specified in 'required_together_fields'
    became required. That is ine can leave all required together fields empty or fill tem all.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #  In case wrong field names are in required_together_fields.
        if not self.fields.keys() >= set(self.required_together_fields):
            raise serializers.ValidationError(
                {'required_together_fields': error_codes.REQUIRED_TOGETHER_WRONG_FIELDS_NAMES.message},
                code=error_codes.REQUIRED_TOGETHER_WRONG_FIELDS_NAMES.code
            )
        #  Check whether or not at least one field from 'required_together_fields' is filled with data.
        try:
            required_fields_in_data = set(self.required_together_fields).intersection(self.initial_data)
        except AttributeError:  # if no initial date in serializer...
            pass
        else:
            if required_fields_in_data:
                for field_name, field in self.fields.items():
                    if field_name in self.required_together_fields:
                        field.required = True

    required_together_fields = ()


class ReadOnlyRaisesException:
    """
    Mixin changes standard serializer behaviour when serializer does not raises errors when fields with read only
    attribute set to True are provided in incoming data to opposite behaviour.
    If at leas one of read_only fields in initial data - validation Error is arisen.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _fields = MappingProxyType(self.fields)
        _read_only_fields = frozenset(field_name for field_name, field in _fields.items() if field.read_only)
        try:
            _initial_data = MappingProxyType(self.initial_data)
            _read_only_fields_in_data = _read_only_fields.intersection(_initial_data)
        except AttributeError:  # if no initial date in serializer...
            pass
        else:
            if _read_only_fields_in_data:
                raise serializers.ValidationError(
                    {field: error_codes.READ_ONLY.message for field in _read_only_fields_in_data},
                    code=error_codes.READ_ONLY.code
                )


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
        # Slave account cant be equal to master account.
        if slave == master:
            raise serializers.ValidationError(
                {'slave_email': error_codes.MASTER_OF_SELF.message},
                code=error_codes.MASTER_OF_SELF.code
            )
        # Master cant be slave.
        if master.is_slave:
            raise serializers.ValidationError(
                {'slave_email': error_codes.SLAVE_CANT_HAVE_SALVES.message},
                code=error_codes.SLAVE_CANT_HAVE_SALVES.code
            )
        # Check whether potential slave is available for this role.
        if not slave.is_available_slave:
            raise serializers.ValidationError(
                {'slave_email': error_codes.SLAVE_UNAVAILABLE.message},
                code=error_codes.SLAVE_UNAVAILABLE.code,
            )