from rest_framework import serializers

from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model

from djoser import serializers as djoser_serializers

from series import error_codes
from users.helpers import serializer_mixins


class CustomDjoserUserCreateSerializer(
        serializer_mixins.ConditionalRequiredPerFieldMixin,
        djoser_serializers.UserCreateSerializer):
    """
    Serializer for create_user action.
    """
    master_email = serializers.EmailField(
        required=False,
        validators=(EmailValidator, ),
        error_messages={'required': error_codes.MASTER_FIELDS_REQUIRED},
        write_only=True,
    )
    master_password = serializers.CharField(
        write_only=True,
        required=False,
        validators=(validate_password, ),
        error_messages={'required': error_codes.MASTER_FIELDS_REQUIRED},
    )
    # не работает валидация модели.
    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        # add possibility to specify 'country' field during user creation.
        fields = djoser_serializers.UserCreateSerializer.Meta.fields + (
            'user_country', 'master_email', 'master_password',
        )
        extra_kwargs = {
            'user_country': {
                'error_messages': {
                    'invalid_choice': error_codes.WRONG_COUNTRY_CODE,
                }}}

    def is_master_password_required(self):
        """
        Turns 'master_password' field to REQUIRED if one of master fields is present in raw incoming data.
        """
        master_email = self.initial_data.get('master_email', False)
        return bool(master_email)

    def is_master_email_required(self):
        """
        Turns 'master_email' field to REQUIRED if one of master fields is present in raw incoming data.
        """
        master_password = self.initial_data.get('master_password', False)
        return bool(master_password)

    @staticmethod
    def validate_master_fields(master_email, master_password):
        """
        Validation process for fields 'master_email' and 'master_password'.
        """
        try:
            master = get_user_model().objects.get(email=master_email)
        except get_user_model().DoesNotExist as err:
            raise serializers.ValidationError(
                {'master_email': error_codes.USER_DOESNT_EXISTS},
                code="doesn't_exists",
            ) from err
        else:
            if not master.check_password(master_password):
                raise serializers.ValidationError(
                    {'master_password': f'Incorrect password for user with {master_email =}'},
                    code='invalid',
                )
            return master

    def validate(self, attrs):
        master_email = attrs.pop('master_email', False)
        master_password = attrs.pop('master_password', False)
        attrs = super().validate(attrs)

        if master_email and master_password:
            master = self.validate_master_fields(master_email, master_password)
            attrs['master'] = master
        return attrs

    def to_representation(self, instance):
        """
        Add 'master_id' key to returned data in case current account saved as slave account.
        """
        data = super().to_representation(instance)
        try:
            master_id = instance.master_id
        except AttributeError:
            return data
        else:
            data.update({'master_id': master_id})
            return data




