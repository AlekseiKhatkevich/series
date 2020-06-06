import unittest

from django.contrib.auth import tokens
from djoser import utils
from rest_framework import serializers
from rest_framework.test import APITestCase

from users.helpers import create_test_users, serializer_mixins


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

    def test_check_password(self):
        """
        Checks correct work of the method 'check_password'.
        """
        self.user_1.set_password('test_password_12345')

        self.assertIsNone(
            serializer_mixins.UserSlaveMutualValidationMixin.check_password(
                self.user_1, 'test_password_12345'
            ))
