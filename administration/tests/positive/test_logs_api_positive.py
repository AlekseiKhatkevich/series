import more_itertools
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from users.helpers import create_test_users


class LogsAPIPositiveTest(APITestCase):
    """
    Positive tests for logs api list view /administration/logs/ GET.
    """
    maxDiff = None
    fixtures = ('logs_dump.json', )

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        cls.admin = more_itertools.first_true(cls.users, pred=lambda user: user.is_staff)

    def test_list_api(self):
        """
        Check that list view logs api works correctly.
        """

        self.client.force_authenticate(self.admin)

        response = self.client.get(
            reverse('logs'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            all(
                [isinstance(log['level'], str) for log in response.data['results']]
            ))

        self.assertSetEqual(
            {'logger_name', 'level', 'msg', 'trace', 'create_datetime', },
            set(response.data['results'][0].keys()),
        )

    # def test_cache_invalidation_LogsListView(self):
    #     """
    #     Check that 'LogsListView' displays new version of page when list of objects is updated(
    #     added or deleted one or more objects).
    #     Check that ETAGs changes after lost of objects got changed
    #     """
    #     self.client.force_authenticate(self.admin)
    #
    #     response_1 = self.client.get(
    #         reverse('logs'),
    #         data=None,
    #         format='json',
    #     )
    #
    #     StatusLog.objects.last().delete()
    #
    #     response_2 = self.client.get(
    #         reverse('logs'),
    #         data=None,
    #         format='json',
    #     )
    #
    #     self.assertNotEqual(
    #         response_1.data,
    #         response_2.data,
    #     )
    #     self.assertNotEqual(
    #         response_1['ETag'],
    #         response_2['ETag'],
    #     )



