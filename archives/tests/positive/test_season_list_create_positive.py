import itertools
import operator

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class TvSeriesListCreatePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on SeasonModel list/create api.
    archives/tvseries/<int:series_pk/seasons/ GET, POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.seasons = initial_data.create_seasons(self.series, num_episodes=3)
        func = operator.attrgetter('series_id')
        data = sorted(self.seasons, key=func)
        self.seasons_dict = {
            key: list(group) for key, group in itertools.groupby(data, func)
        }
        for series_id, seasons in self.seasons_dict.items():
            for season in seasons:
                setattr(self, f'season_{series_id}_{season.season_number}', season)

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