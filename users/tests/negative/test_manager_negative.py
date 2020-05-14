from rest_framework.test import APITestCase
from django.core import exceptions
from django.contrib.auth import get_user_model
from series import error_codes
from users.helpers import create_test_users


class UserManagerAndQuerysetNegativeTest(APITestCase):
    """
    Test for User model manager and queryset methods(negative).
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_check_user_and_password_method_gets_wrong_user_email(self):
        """
        Checks whether 'check_user_and_password' raises Validation error in case it receives
        email argument that does not exists in DB.
        """
        expected_error_message = error_codes.USER_DOESNT_EXISTS.message

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            get_user_model().objects.check_user_and_password(
                email='wrong_email',
                password='wrong_password',
            )

    def test_check_user_and_password_method_gets_wrong_user_password(self):
        """
        Checks whether 'check_user_and_password' raises Validation error in case it receives
        email argument that does not exists in DB.
        """
        expected_error_message = f'Incorrect password for user with email - {self.user_1.email}'

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            get_user_model().objects.check_user_and_password(
                email=self.user_1.email,
                password='wrong_password',
            )
