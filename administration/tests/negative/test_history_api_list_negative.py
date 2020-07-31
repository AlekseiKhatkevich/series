from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users


class HistoryAPIListNegativeTest(APITestCase):
    """
    Negative tests on models change history api list action
    administration/history/<model name>/<pk/.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def test_access_forbidden_for_random_users(self):
        """
        Check that users who dont have defined permissions can not access this API endpoint.
        """
        test_series = self.series_1
        self.client.force_authenticate(user=self.series_2.entry_author)

        response = self.client.get(
            reverse('history-list', args=['tvseriesmodel', test_series.pk]),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_404_on_non_existent_instances(self):
        """
        Check that if instance does not exists, than 404 exception will be raised.
        """
        random_pk = max(self.series_1.pk, self.series_2.pk) + 9999999

        response = self.client.get(
            reverse('history-list', args=['tvseriesmodel', random_pk]),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
