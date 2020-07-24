from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class LogsAPINegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative tests for logs api list view /administration/logs/ GET.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_not_admin_can_not_access(self):
        """
        Check that non-admins can't access api endpoint.
        """
        expected_error_message = error_codes.DRF_NO_PERMISSIONS.message

        self.client.force_authenticate(self.user_3)

        response = self.client.get(
            reverse('logs'),
            data=None,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=expected_error_message,
            field='detail',
        )

