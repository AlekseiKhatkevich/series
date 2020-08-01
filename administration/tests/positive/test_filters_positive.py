import more_itertools
from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from administration.helpers.initial_data import generate_changelog
from archives.tests.data import initial_data
from series.helpers import custom_functions
from users.helpers import create_test_users
from administration.models import UserStatusChoices, OperationTypeChoices


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
            all(log['level'] in ('Error', 'Fatal',) for log in response.data['results'])
        )


class HistoryViewSetFiltersPositiveTest(APITestCase):
    """
    Positive tests for filters on 'HistoryViewSet' in 'administration' app.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.logs = generate_changelog(cls.series_1, cls.users, num_logs=50, )

    def setUp(self) -> None:
        self.query_dict_1 = QueryDict(mutable=True)
        self.query_dict_2 = QueryDict(mutable=True)

    def test_filter_by_as_who_or_operation_type(self):
        """
        Check that 'as_who' and 'operation_type' filter filters out entries by
        'as_who' or 'operation_type' filed.
        """
        self.query_dict_1['as_who'] = UserStatusChoices.CREATOR
        self.query_dict_2['operation_type'] = OperationTypeChoices.CREATE

        self.client.force_authenticate(user=self.series_1.entry_author)

        for filter_param, query_dict in zip(
                ('as_who', 'operation_type',),
                (self.query_dict_1, self.query_dict_2,),
        ):
            with self.subTest(filter_param=filter_param, query_dict=query_dict):

                response = self.client.get(
                    reverse(
                        'history-list',
                        args=['tvseriesmodel', self.series_1.pk, ]
                            ) + '?' + query_dict.urlencode(),
                    data=None,
                    format='json',
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )
                self.assertTrue(
                    all(log[filter_param] == query_dict[filter_param]
                        for log in response.data['results']
                        ))
