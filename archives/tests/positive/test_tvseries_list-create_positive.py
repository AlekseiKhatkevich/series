from drf_extra_fields.fields import DateRangeField
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.helpers import custom_functions
from users.helpers import create_test_users


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
        initial_data.create_images_instances((self.series_1, ))

        self.seasons = initial_data.create_seasons(self.series)
        self.overall_number_of_episodes = sum((season.number_of_episodes for season in self.seasons))

        self.data = {
            'translation_years': {'lower': '2020-01-01'},
            'name': 'test-test',
            'imdb_url': 'https://www.imdb.com/',
            'interrelationship': [
                {
                    'name': self.series_1.name,
                    'reason_for_interrelationship': 'test1'
                },
                {
                    'name': self.series_2.name,
                    'reason_for_interrelationship': 'test1'
                }]}

    def test_list_action(self):
        """
        Check that correct response with correct data is received on Get request.
        """
        self.series_1.interrelationship.add(
            self.series_2,
            through_defaults={
                'reason_for_interrelationship': 'test'
            })

        response = self.client.get(
            reverse('tvseries'),
            data=None,
            format='json',
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.series_1.entry_author.get_full_name(),
            response_data[self.series_1.pk]['entry_author']
        )
        self.assertEqual(
            self.series_1.group.first().reason_for_interrelationship,
            response_data[self.series_1.pk]["interrelationship"][0]["reason_for_interrelationship"]
        )
        self.assertIsNotNone(
            response_data[self.series_1.pk]['images'][0]['image']
        )
        self.assertEqual(
            self.overall_number_of_episodes,
            sum((season['number_of_episodes'] for season in response_data.values()))
        )
        self.assertEqual(
            len(self.seasons),
            sum((season['number_of_seasons'] for season in response_data.values()))
        )
        self.assertEqual(
            DateRangeField().to_representation(self.series_1.translation_years),
            response_data[self.series_1.pk]['translation_years']
        )

    def test_nullif(self):
        """
        Check that if season have zero episodes, then 'number_of_seasons' field would be filed
        with Null(none) instead of default 0.
        """
        self.series_1.seasons.all().delete()

        response = self.client.get(
            reverse('tvseries'),
            data=None,
            format='json',
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertIsNone(
            response_data[self.series_1.pk]['number_of_seasons']
        )

    def test_create_action(self):
        """
        Check that if correct input data is provided - then endpoint is able to successfully create
        model instances.
        """
        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            reverse('tvseries'),
            data=self.data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        series = archives.models.TvSeriesModel.objects.filter(name=self.data['name'])

        self.assertTrue(
            series.exists()
        )

        series = series.get()

        self.assertListEqual(
            list(series.interrelationship.all().values_list('pk', flat=True)),
            [series.pk for series in self.series],
        )

