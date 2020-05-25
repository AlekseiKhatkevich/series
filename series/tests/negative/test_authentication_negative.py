from unittest import skipIf

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

import series.authentication
from series import error_codes
from series.helpers.test_helpers import TestHelpers
from users.helpers import create_test_users


class AuthenticationNegativeTest(APITestCase):
    """
    Test on custom auth JWT backend. Test that requests or users that aren't coincide to specific conditions
    aren't allowed.
    """
    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, *rest = self.users

    @skipIf(series.authentication.SoftDeletedJWTAuthentication not in
            api_settings.DEFAULT_AUTHENTICATION_CLASSES, 'JWT auth is off')
    def test_deleted_user_is_not_allowed(self):
        """
        Check that soft-deleted user's request will be rejected.
        """
        self.user_1.delete()
        access_token = self.user_1.get_tokens_for_user()['access']
        expected_error_message = error_codes.USER_IS_DELETED.message
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(
            reverse('user-me'),
            data=None,
            format='json',
        )

        TestHelpers().check_status_and_error(
            response,
            field='detail',
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_message=expected_error_message,
        )
