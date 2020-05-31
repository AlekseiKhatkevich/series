from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.validators import EmailValidator
from djoser import serializers as djoser_serializers
from rest_framework import exceptions as drf_exceptions, serializers
from djoser.conf import settings as djoser_settings
from series import error_codes
from users.helpers import serializer_mixins, validators as custom_validators


class CustomDjoserUserCreateSerializer(
    serializer_mixins.RequiredTogetherFieldsMixin,
    djoser_serializers.UserCreateSerializer):
    """
    Serializer for create_user action.
    """
    master_email = serializers.EmailField(
        required=False,
        write_only=True,
        validators=(EmailValidator,),
        error_messages={'required': error_codes.MASTER_FIELDS_REQUIRED.message},
    )
    master_password = serializers.CharField(
        required=False,
        write_only=True,
        validators=(validate_password,),
        error_messages={'required': error_codes.MASTER_FIELDS_REQUIRED.message},
    )

    required_together_fields = ('master_password', 'master_email',)

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        # add possibility to specify 'country' field during user creation.
        # add possibility to specify fields necessary to attach created account as a salve one.
        fields = djoser_serializers.UserCreateSerializer.Meta.fields + (
            'user_country', 'master_email', 'master_password',
        )
        extra_kwargs = {
            'email': {'validators': [
                custom_validators.UserUniqueValidator(
                    queryset=get_user_model()._default_manager.all()
                )]},
            'user_country': {
                'error_messages': {
                    'invalid_choice': error_codes.WRONG_COUNTRY_CODE.message,
                }}}

    def validate(self, attrs):
        master_email = attrs.pop('master_email', False)
        master_password = attrs.pop('master_password', False)
        attrs = super().validate(attrs)

        if master_email and master_password:
            master = self.Meta.model.objects.check_user_and_password(master_email, master_password)
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


class CustomUserSerializer(
    serializer_mixins.ReadOnlyRaisesException,
    djoser_serializers.UserSerializer
):
    """
    Serializer for endpoint that shows list of users for Admin or user detail for current user
    if it not an admin.
    """

    class Meta(djoser_serializers.UserSerializer.Meta):
        fields = djoser_serializers.UserSerializer.Meta.fields + ('user_country', 'master', )
        read_only_fields = djoser_serializers.UserSerializer.Meta.read_only_fields + ('master', )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if self.context['view'].action != 'list':
            data['slave_accounts_ids'] = instance.slaves.all().values_list('pk', flat=True) or None
        return data


class SetSlavesSerializer(
    serializer_mixins.UserSlaveMutualValidationMixin,
    serializers.Serializer
):
    """
    Serializer for setting one account as a slave of master account.
    action - 'set_slaves'.
    """

    slave_email = serializers.EmailField(
        write_only=True,
        validators=(EmailValidator,),
        error_messages={'required': error_codes.SLAVE_FIELDS_REQUIRED.message},
    )
    slave_password = serializers.CharField(
        write_only=True,
        validators=(validate_password,),
        error_messages={'required': error_codes.SLAVE_FIELDS_REQUIRED.message},
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    def validate(self, attrs):
        slave_email = attrs['slave_email']
        slave_password = attrs['slave_password']
        user = attrs['user']

        # Validates potential slave's email and password.
        self.slave = get_user_model().objects.check_user_and_password(slave_email, slave_password)
        self.master_slave_mutual_data_validation(slave=self.slave, master=user)
        return super().validate(attrs)

    def create(self, validated_data):
        self.slave.master = validated_data['user']
        self.slave.save()
        return self.slave


class UndeleteUserAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for undelete user account action.
    """

    class Meta:
        model = get_user_model()
        fields = ('email', 'password',)
        write_only_fields = fields
        extra_kwargs = {
            'email': {'validators': (EmailValidator,)},
            'password': {'validators': (validate_password,)}
        }

    def validate(self, attrs):
        email, password = attrs['email'], attrs['password']
        self.soft_deleted_user = get_user_model().objects.check_user_and_password(
            email, password, include_soft_deleted=True,
        )
        if not self.soft_deleted_user.deleted:
            raise serializers.ValidationError(
                {'email': error_codes.NOT_SOFT_DELETED.message},
                code=error_codes.NOT_SOFT_DELETED.code,
            )
        return super().validate(attrs)

    def create(self, validated_data):
        self.soft_deleted_user.deleted = False
        self.soft_deleted_user.save(update_fields=('deleted',))
        return self.soft_deleted_user


class CommitUndeleteUserAccountSerializer(
    serializer_mixins.UidAndTokenValidationMixin,
    djoser_serializers.UidAndTokenSerializer
):
    """
      Serializer to undelete user when 'SEND_ACTIVATION_EMAIL' flag is set to True. In this case user
      receives an email with confirmation link, clicks it, frontend parses this link, extracts
      uid and token from it and sends to backend via POST request.
    """

    def validate(self, attrs):
        uid = self.initial_data.get('uid', '')
        self.user = self.confirm_uid(uid)

        if not self.user.deleted:
            raise serializers.ValidationError(
                {'uid': error_codes.NOT_SOFT_DELETED.message},
                code=error_codes.NOT_SOFT_DELETED.code,
            )

        token = self.initial_data.get('token', '')
        self.confirm_token(user=self.user, token=token)

        return attrs


class CommitSetSlavesSerializer(
    serializer_mixins.UserSlaveMutualValidationMixin,
    serializer_mixins.UidAndTokenValidationMixin,
    serializers.Serializer,
):
    """
    Serializer receives slave and master uid, token , validates it and attaches slave to master.
    Needed to confirm slave attachment when user clicks confirmation link in email.
    confirmation url example -MQ/Mg/5gt-5ac6b80063a4457b88a7
    """

    master_uid = serializers.CharField()
    slave_uid = serializers.CharField()
    token = serializers.CharField()

    def validate_master_uid(self, value):
        self.master = self.confirm_uid(uid=value)
        return value

    def validate_slave_uid(self, value):
        self.slave = self.confirm_uid(uid=value)
        return value

    def validate_token(self, value):
        self.confirm_token(user=self.slave, token=value)
        return value

    def validate(self, attrs):
        self.master_slave_mutual_data_validation(master=self.master, slave=self.slave)
        return super().validate(attrs)

    def create(self, validated_data):
        self.slave.master = self.master
        self.slave.save()
        return self.slave
