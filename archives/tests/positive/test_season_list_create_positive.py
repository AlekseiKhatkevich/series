import datetime

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users
import archives.models


class TvSeriesListCreatePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on SeasonModel list/create api.
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

    def test_list_view(self):
        """
        Check that api endpoint archives/tvseries/<int:series_pk/seasons/ GET
        works correctly in general.
        """
        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('seasonmodel-list', args=(self.series_1.pk,)),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertListEqual(
            [season.pk for season in self.seasons_dict[self.series_1.pk]],
            [element['pk'] for element in response.data['results']],
        )

    def test_create_view(self):
        """
        Check that if correct date is provided, seasons can be created successfully.
        """
        test_series = self.series_1
        test_series.seasons.all().delete()
        tr_lower = test_series.translation_years.lower + datetime.timedelta(days=1)
        tr_upper = test_series.translation_years.lower + datetime.timedelta(days=300)

        data = {
            'season_number': 1,
            'number_of_episodes': 10,
            'last_watched_episode': 2,
            'episodes': {
                '1': (tr_lower + datetime.timedelta(days=1)).isoformat(),
                '2': (tr_lower + datetime.timedelta(days=10)).isoformat(),
            },
            'translation_years': {
                'lower': tr_lower.isoformat(),
                'upper': tr_upper.isoformat(),
                'bounds': '[]',
            }}

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.post(
            reverse('seasonmodel-list', args=(test_series.pk,)),
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            archives.models.SeasonModel.objects.filter(
                pk=response.data['pk'],
                series=test_series,
            ).exists()
        )
