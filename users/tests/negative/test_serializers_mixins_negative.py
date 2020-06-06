from django.contrib.auth import tokens
from djoser import utils
from rest_framework import serializers
from rest_framework.test import APITestCase

from users.helpers import create_test_users, serializer_mixins


class UidAndTokenValidationMixinNegativeTest(APITestCase):
    """
    Negative test on 'UidAndTokenValidationMixin' functionality.
    """
    @classmethod
    def setUpTestData(cls):
        cls.mixin = serializer_mixins.UidAndTokenValidationMixin()
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        for user in cls.users:
            setattr(user, 'uid', utils.encode_uid(user.pk))
            setattr(user, 'token', tokens.default_token_generator.make_token(user))

    def test_confirm_uid_wrong_uid(self):
        """
        Check that if incorrect uid is provided, then validation error is arisen.
        """
        wrong_uid = 'MQ'
        expected_error_message = str(self.mixin.default_error_messages['invalid_uid'])

        with self.assertRaisesMessage(serializers.ValidationError, expected_error_message):
            self.mixin.confirm_uid(wrong_uid)

    def test_confirm_token_wrong_token(self):
        """
        Check that if incorrect token is provided, then validation error is arisen.
        """
        wrong_token = 'wrong_token'
        expected_error_message = str(self.mixin.default_error_messages['invalid_token'])

        with self.assertRaisesMessage(serializers.ValidationError, expected_error_message):
            self.mixin.confirm_token(self.user_1, wrong_token)

    def test_check_password_raises_message(self):
        """
        Checks if method 'check_password' receives wrong password, then validation error is arisen.
        """
        expected_error_message = f'Incorrect password for slave with email - {self.user_1.email}'

        with self.assertRaisesMessage(serializers.ValidationError, expected_error_message):
            serializer_mixins.UserSlaveMutualValidationMixin.check_password(
                self.user_1, 'random_password')
