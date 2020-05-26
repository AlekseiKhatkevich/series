import unittest

from django.contrib.auth import tokens
from djoser import utils
from rest_framework import exceptions as drf_exceptions, serializers
from rest_framework.test import APISimpleTestCase, APITestCase

from series import error_codes
from users.helpers import create_test_users, serializer_mixins


class SerializersMixinPositiveTest(APISimpleTestCase):
    """
    Test custom serializers mixins.
    """

    class TestSerializer(
            serializer_mixins.RequiredTogetherFieldsMixin,
            serializers.Serializer):
        field_1 = serializers.CharField(max_length=10, required=True)
        field_2 = serializers.IntegerField(required=False)
        field_3 = serializers.EmailField(required=False)

        required_together_fields = ('field_2', 'field_3',)

    def test_RequiredTogetherFieldsMixin(self):
        """
        Check whether or not 'RequiredTogetherFieldsMixin' would allow to mark set of fields as
        required together fields.
        """
        #  Fill only first required field. 2 other fields should stay non-required.
        data = {'field_1': 'test'}
        serializer = self.TestSerializer(data=data)

        self.assertTrue(
            serializer.is_valid()
        )
        self.assertFalse(
            all(field.required for field_name, field in serializer.fields.items())
        )

        #  Fill first required field and one of required_together_fields.
        #  All fields should turn required=True.
        data = {'field_1': 'test', 'field_2': 10}
        serializer = self.TestSerializer(data=data)

        self.assertFalse(
            serializer.is_valid()
        )
        self.assertTrue(
            all(field.required for field_name, field in serializer.fields.items())
        )

        # Fill all 3 fields. All fields should turn required=True.
        data = {'field_1': 'test', 'field_2': 10, 'field_3': 'email@email.com'}
        serializer = self.TestSerializer(data=data)

        self.assertTrue(
            serializer.is_valid()
        )
        self.assertTrue(
            all(field.required for field_name, field in serializer.fields.items())
        )

    class TestSerializer_2(
            serializer_mixins.ReadOnlyRaisesException,
            serializers.Serializer):
        field_1 = serializers.CharField(max_length=10, read_only=True)
        field_2 = serializers.IntegerField()
        field_3 = serializers.EmailField()

    def test_ReadOnlyRaisesException_mixin(self):
        """
        Check that in case one or more read_only fields are in initial data, serializer would
        not be validated.
        """
        data = {'field_1': 'test', 'field_2': 1, 'field_3': 'user@imbox.ru'}

        with self.assertRaisesMessage(serializers.ValidationError, error_codes.READ_ONLY.message):
            self.TestSerializer_2(data=data)


class UidAndTokenValidationMixinPositiveTest(APITestCase):
    """
    Positive test on 'UidAndTokenValidationMixin' functionality.
    """
    @classmethod
    def setUpTestData(cls):
        cls.mixin = serializer_mixins.UidAndTokenValidationMixin()
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        for user in cls.users:
            setattr(user, 'uid', utils.encode_uid(user.pk))
            setattr(user, 'token', tokens.default_token_generator.make_token(user))

    def test_confirm_uid(self):
        """
        Check that if correct uid is provided, then method returns user instance object correspondent with
        the given uid.
        """
        returned_user_instance = self.mixin.confirm_uid(self.user_1.uid)

        self.assertEqual(
            returned_user_instance,
            self.user_1
        )

    @unittest.expectedFailure
    def test_confirm_token(self):
        """
        Check that if correct token is provided, then method doesn't raise validation error.
        '5gt-0b56f67cea6894179444' -token example
        """
        with self.assertRaises(serializers.ValidationError):
            self.mixin.confirm_token(self.user_1, self.user_1.token)
