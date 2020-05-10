from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from djoser import serializers as djoser_serializers
from rest_framework import serializers

from series import error_codes
from users.helpers import serializer_mixins


class CustomDjoserUserCreateSerializer(
        serializer_mixins.RequiredTogetherFieldsMixin,
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

    required_together_fields = ('master_password', 'master_email', )

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        # add possibility to specify 'country' field during user creation.
        # add possibility to specify fields necessary to attach created account as a salve one.
        fields = djoser_serializers.UserCreateSerializer.Meta.fields + (
            'user_country', 'master_email', 'master_password',
        )
        extra_kwargs = {
            'user_country': {
                'error_messages': {
                    'invalid_choice': error_codes.WRONG_COUNTRY_CODE,
                }}}

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
        Add 'master_id' key to returned data.
        """
        data = super().to_representation(instance)
        try:
            data['master_id'] = instance.master_id
        except AttributeError:
            pass
        return data






