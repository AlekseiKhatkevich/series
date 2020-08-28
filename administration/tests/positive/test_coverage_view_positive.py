import more_itertools
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.helpers import create_test_users


class CoveragePositiveTest(APITestCase):
    """
    Positive test on 'coverage_view' in 'administration' app.
    """

    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.admin = more_itertools.first_true(cls.users, pred=lambda user: user.is_staff)

    def test_response(self):
        """
        Check that 'coverage_view' returns coverage data in json.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse('coverage'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIsNotNone(
            response.data
        )
