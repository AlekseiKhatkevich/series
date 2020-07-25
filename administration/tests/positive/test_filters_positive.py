import more_itertools
from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.helpers import create_test_users


class LogsFiltersPositiveTest(APITestCase):
    """
    Positive tests for filters on LogsListView in 'administration' app.
    """
    maxDiff = None
    fixtures = ('logs_dump.json',)

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        cls.admin = more_itertools.first_true(cls.users, lambda user: user.is_staff)

    def setUp(self) -> None:
        self.query_dict = QueryDict(mutable=True)

    def test_filter_by_logger_name(self):
        """
        Check that logs can be filtered by logger name.
        """
        self.query_dict['logger_name'] = 'django.request'

        self.client.force_authenticate(self.admin)

        response = self.client.get(
            reverse('logs') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            all(log['logger_name'] == 'django.request' for log in response.data['results'])
        )

    def test_filter_by_level(self):
        """
        Check that logs can be filtered by level.
        """
        self.query_dict['level__gte'] = 40

        self.client.force_authenticate(self.admin)

        response = self.client.get(
            reverse('logs') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            all(log['level'] in ('Error', 'Fatal', ) for log in response.data['results'])
        )
