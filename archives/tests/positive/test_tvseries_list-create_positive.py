from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users
from series.helpers import custom_functions


class TvSeriesListCreatePositiveTest(APITestCase):
    """
    Positive test on TVSeries model list-create API endpoint.
    archives/tvseries/ GET or POST.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def setUp(self) -> None:
        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

    def test_list_action(self):
        """
        Check that correct response with correct data is received on Get request.
        """
        self.series_1.interrelationship.add(
            self.series_2,
            through_defaults={
                'reason_for_interrelationship': 'test'
            }
        )

        response = self.client.get(
            reverse('tvseries'),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            self.series_1.entry_author.get_full_name(),
            response_data[self.series_1.pk]['entry_author']
        )

        self.assertEqual(
            self.series_1.group.first().reason_for_interrelationship,
            response_data[self.series_1.pk]["interrelationship"][0]["reason_for_interrelationship"]
        )
        self.assertEqual(
            self.series_1.images
        )