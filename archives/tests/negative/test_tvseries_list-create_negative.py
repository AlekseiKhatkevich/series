from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users
from series.helpers import custom_functions, test_helpers


class TvSeriesListCreateNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test on TVSeries model list-create API endpoint.
    archives/tvseries/ GET or POST.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def setUp(self) -> None:
        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series
        initial_data.create_images_instances((self.series_1,))

        self.seasons = initial_data.create_seasons(self.series)

        self.data = {
            'name': 'test-test',
            'imdb_url': 'https://www.imdb.com/video/vi2805579289?ref_=hp_hp_e_2&listId=ls025720609',
            'interrelationship': [
                {
                    'name': self.series_1.name,
                    'reason_for_interrelationship': 'test1'
                }]}

    def test_check_permissions(self):
        """
        Check that only authenticated users can perform create action.
        """
        response = self.client.post(
            reverse('tvseries'),
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message='Authentication credentials were not provided.',
            field='detail'
        )

    def test_cant_arrange_interrelationship_on_itself(self):
        """
        Check that freshly created season can't have m2m interrelationship on itself.
        """
        self.data['interrelationship'][0]['name'] = 'test-test'
        expected_error_message = 'Object with name=test-test does not exist.'

        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            reverse('tvseries'),
            data=self.data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            str(response.data['interrelationship'][0]['name'][0]),
            expected_error_message,
        )


