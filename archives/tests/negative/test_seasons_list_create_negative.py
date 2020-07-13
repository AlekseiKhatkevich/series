from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class TvSeriesListCreateNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test case on SeasonModel list/create api.
    archives/tvseries/<int:series_pk/seasons/ GET, POST
    """

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
