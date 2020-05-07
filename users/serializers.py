from djoser import serializers as djoser_serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomDjoserUserCreateSerializer(djoser_serializers.UserCreateSerializer):
    """
    Serializer for create_user action.
    """

    class Meta(djoser_serializers.UserCreateSerializer.Meta):
        # add possibility to specify 'country' field during user creation.
        fields = djoser_serializers.UserCreateSerializer.Meta.fields + ('user_country',)
        extra_kwargs = {
            'user_country': {
                'error_messages': {
                    'invalid_choice': 'Wrong country code. Country code should consist of 2 '
                                      'uppercase letters according ISO 3166',
                }}}

