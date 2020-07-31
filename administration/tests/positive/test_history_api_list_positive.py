from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from administration.helpers.initial_data import generate_changelog
from archives.tests.data import initial_data
from series.helpers import custom_functions
from users.helpers import create_test_users


class HistoryAPIPositiveTest(APITestCase):
    """
    Positive tests on models change history api list action
    administration/history/<model name>/<pk/.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        initial_data.create_images_instances((cls.series_1, ))

        cls.seasons = initial_data.create_seasons(cls.series, return_sorted=True)
        cls.seasons, cls.seasons_dict = cls.seasons

    def test_list_action_series(self):
        """
        Check that for each type of model api returns EntriesChangeLog entries devoted to this
        exact model and to model's instance specified in url kwargs pk.
        TvSeriesModel
        """
        test_series = self.series_1
        generate_changelog(test_series, self.user_1, )

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.get(
            reverse('history-list', args=['tvseriesmodel', test_series.pk]),
            data=None,
            format='json',
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            set(test_series.access_logs.all().values_list('pk', flat=True)),
            set(response_data.keys()),
        )
        self.assertSetEqual(
            {log['user'] for log in response_data.values()},
            {self.user_1.email, },
        )

    def test_list_action_seasons(self):
        """
        Check that for each type of model api returns EntriesChangeLog entries devoted to this
        exact model and to model's instance specified in url kwargs pk.
        SeasonModel
        """
        test_season, *rest = self.seasons
        generate_changelog(test_season, self.user_2, )

        self.client.force_authenticate(user=test_season.entry_author)

        response = self.client.get(
            reverse('history-list', args=['seasonmodel', test_season.pk]),
            data=None,
            format='json',
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            set(test_season.access_logs.all().values_list('pk', flat=True)),
            set(response_data.keys()),
        )
        self.assertSetEqual(
            {log['user'] for log in response_data.values()},
            {self.user_2.email, },
        )

    def test_list_action_images(self):
        """
        Check that for each type of model api returns EntriesChangeLog entries devoted to this
        exact model and to model's instance specified in url kwargs pk.
        Check that if request user has rights to access series , than he as well has rights to access
        corespondent image's history.
        ImageModel
        """
        test_image = self.series_1.images.first()
        generate_changelog(test_image, self.user_3, )

        #  Series to which image is belong should have an access to history API endpoint.
        self.client.force_authenticate(user=self.series_1.entry_author)

        response = self.client.get(
            reverse('history-list', args=['imagemodel', test_image.pk]),
            data=None,
            format='json',
        )

        response_data = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            set(test_image.access_logs.all().values_list('pk', flat=True)),
            set(response_data.keys()),
        )
        self.assertSetEqual(
            {log['user'] for log in response_data.values()},
            {self.user_3.email, },
        )





