from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
import archives.models
from archives.tests.data import initial_data
from series import constants
from series.helpers import test_helpers
from users.helpers import create_test_users


class SeasonsDetailPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on SeasonModel detail api.
    archives/tvseries/<int:series_pk/seasons/<int:pk> GET, DELETE, PATCH, PUT
    """
    maxDiff = None

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

        self.seasons, self.seasons_dict = initial_data.create_seasons(
            self.series,
            num_seasons=3,
            return_sorted=True,
        )
        self.season_1_1, self.season_1_2, self.season_1_3, *series_2_seasons = self.seasons

    def test_detail_api(self):
        """
        Check that detail api works and returns status 200.
        """
        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            self.season_1_1.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['series_name'],
            self.season_1_1.series.name,
        )
        self.assertNotIn(
            'days_until_free_access',
            response.data,
        )

    def test_days_until_free_access_is_shown(self):
        """
        Check that 'days_until_free_access' field is shown if author is soft-deleted and his does not
        have any alive slaves or master.
        """
        test_season = self.season_1_3
        author = test_season.entry_author

        author.delete()

        self.client.force_authenticate(user=self.user_2)

        response = self.client.get(
            test_season.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn(
            'days_until_free_access',
            response.data,
        )

    def test_zero_days_until_free_access_is_shown_if_time_has_elapsed(self):
        """
        Check that zero is shown in a 'days_until_free_access' field if days are elapsed.
        """
        test_season = self.season_1_3
        author = test_season.entry_author

        author.deleted = True
        author.deleted_time = timezone.now() - timezone.timedelta(
            days=(constants.DAYS_ELAPSED_SOFT_DELETED_USER + 100)
        )
        author.save()

        self.client.force_authenticate(user=self.user_2)

        response = self.client.get(
            test_season.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data['days_until_free_access'],
            0,
        )

    def test_delete(self):
        """
        Check that DELETE action deletes chosen season.
        """
        test_season = self.season_1_3
        author = test_season.entry_author

        self.client.force_authenticate(user=author)

        response = self.client.delete(
            test_season.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            archives.models.SeasonModel.objects.filter(pk=test_season.pk).exists()
        )

    def test_update_season(self):
        """
        Check that if correct data is provided, than it is possible to correctly update season
        instance.
        """
        test_season = self.season_1_1
        author = test_season.entry_author

        data = {
            'season_number': test_season.season_number,
            'number_of_episodes': 12,
            'last_watched_episode': 4,
            'episodes': {
                '1': test_season.episodes[1].isoformat(),
                '2': test_season.episodes[2].isoformat(),
            },
            'translation_years': {
                'lower': test_season.translation_years.lower.isoformat(),
                'upper': test_season.translation_years.upper.isoformat(),
                'bounds': '[]',
            }}
        self.client.force_authenticate(user=test_season.entry_author)

        response = self.client.put(
            test_season.get_absolute_url,
            data=data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        test_season.refresh_from_db()

        self.assertEqual(
            test_season.number_of_episodes,
            12,
        )
        self.assertEqual(
            test_season.entry_author,
            author,
        )

        response = self.client.patch(
            test_season.get_absolute_url,
            data=data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )