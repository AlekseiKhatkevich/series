from unittest import skipIf

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.settings import api_settings
from rest_framework.test import APITestCase

import series.authentication
from users.helpers import create_test_users


class AuthenticationPositiveTest(APITestCase):
    """
    Test on custom auth JWT backend. Test that provided correct JWT user can authenticate request.
    """
    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, *rest = self.users

    @skipIf(series.authentication.SoftDeletedJWTAuthentication not in
            api_settings.DEFAULT_AUTHENTICATION_CLASSES, 'JWT auth is off')
    def test_auth(self):
        """
        Check that user with correct JWT can authenticate himself.
        """
        access_token = self.user_1.get_tokens_for_user()['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        response = self.client.get(
            reverse('user-me'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

