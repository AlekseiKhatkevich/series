import more_itertools
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SeasonsListCreateNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test case on SeasonModel list/create api.
    archives/tvseries/<int:series_pk/seasons/ GET, POST
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.seasons, self.seasons_dict = initial_data.create_seasons(
            self.series,
            num_seasons=3,
            return_sorted=True,
        )

    def test_need_authentication(self):
        """
        Check that authentication needed to access list view api endpoint.
        """
        expected_error_message = 'Authentication credentials were not provided.'
        response = self.client.get(
            reverse('seasonmodel-list', args=(self.series_1.pk,)),
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=expected_error_message,
        )

    def test_list_create_view_wrong_series_pk(self):
        """
        Check if wrong 'series_pk' url kwarg is provides after url resolving have taken place, than
        404 error is arisen.
        """
        self.client.force_authenticate(user=self.user_1)
        semi_random_pk = [pk for pk in range(10) if pk not in self.seasons_dict.keys()][0]

        response = self.client.get(
            reverse('seasonmodel-list', args=(semi_random_pk,)),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_random_user_can_not_create(self):
        """
        Check that random user who is not a series author, friend, slave or  master can not create
        season.
        """
        test_series = self.series_2
        random_user = more_itertools.first_true(
            self.users,
            lambda user: user != test_series.entry_author,
        )
        self.assertIsNone(
            random_user.master
        )
        self.assertFalse(
            random_user.slaves.exists()
        )
        self.client.force_authenticate(user=random_user)

        response = self.client.post(
            reverse('seasonmodel-list', args=(test_series.pk, )),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
