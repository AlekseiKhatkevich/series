import datetime
from unittest.mock import Mock, patch

from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class TvSeriesListFiltersTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on SeasonModel list/create api filters.
    archives/tvseries/<int:series_pk/seasons/ GET, POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.query_dict_1 = QueryDict(mutable=True)
        self.query_dict_2 = QueryDict(mutable=True)

        self.seasons, self.seasons_dict = initial_data.create_seasons(
            self.series,
            num_seasons=4,
            return_sorted=True,
        )

    def test_episodes_dates(self):
        """
        Check that filter 'episodes_dates' returns only series which dates contained in chosen
        date range.
        """
        test_series = self.series_1

        test_range_lower = test_series.translation_years.lower
        test_range_upper = test_range_lower + (
                (test_series.translation_years.upper - test_range_lower) / 2)

        self.query_dict_1['episodes_dates_lower'] = test_range_lower.isoformat()
        self.query_dict_1['episodes_dates_upper'] = test_range_upper.isoformat()

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('seasonmodel-list', args=(self.series_1.pk,)) +
            '?' + self.query_dict_1.urlencode(),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            len(self.seasons_dict[test_series.pk]),
            len(response.data['results'])
        )

        for season in response.data['results']:
            with self.subTest(season=season):
                self.assertTrue(
                    any(
                        test_range_lower <= datetime.date.fromisoformat(date) <= test_range_upper
                        for date in season['episodes'].values()
                    ))

    def test_filter_by_user(self):
        """
        Check that 'filter_by_user' filter returns only seasons created by current user or opposite.
        """
        test_series = self.series_1

        self.query_dict_1['filter_by_user'] = True
        self.query_dict_2['filter_by_user'] = False

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.get(
            reverse('seasonmodel-list', args=(test_series.pk,)) +
            '?' + self.query_dict_1.urlencode(),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(self.seasons_dict[test_series.pk]),
            len(response.data['results']),
        )

        response = self.client.get(
            reverse('seasonmodel-list', args=(test_series.pk,)) +
            '?' + self.query_dict_2.urlencode(),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data['results']),
            0,
        )

    def test_is_fully_watched(self):
        """
        Check that 'is_fully_watched' filter returns only fully watched seasons or opposite.
        """
        test_series = self.series_1
        self.query_dict_1['is_fully_watched'] = True

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.get(
            reverse('seasonmodel-list', args=(test_series.pk,)) +
            '?' + self.query_dict_1.urlencode(),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            len(response.data['results']),
            self.seasons_dict[test_series.pk]
        )
        self.assertTrue(
            all(season['is_fully_watched'] for season in response.data['results'])
        )

    def test_has_episodes_this_week(self):
        """
        Check that 'has_episodes_this_week' returns only seasons which have at least one
        episode released during current week.
        """
        self.query_dict_1['has_episodes_this_week'] = True

        test_series = self.series_1
        test_season = self.seasons_dict[test_series.pk][0]

        fake_now = test_season.episodes[1]

        date_mock = Mock(wraps=datetime.date)
        date_mock.today.return_value = fake_now

        with patch('datetime.date', new=date_mock):
            self.client.force_authenticate(user=test_series.entry_author)

            response = self.client.get(
                reverse('seasonmodel-list', args=(test_series.pk,)) +
                '?' + self.query_dict_1.urlencode(),
                data=None,
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )
            self.assertNotEqual(
                len(response.data['results']),
                self.seasons_dict[test_series.pk]
            )
            self.assertTrue(
                all(season.new_episode_this_week for season in response.data['results'])
            )

    def test_filter_by_progress(self):
        """
        Check that 'filter_by_progress' returns seasons filtered by last_watched_episode divided
        by number_of_episodes ratio.
        """
        test_series = self.series_1

        ratio = max(
            season.last_watched_episode/season.number_of_episodes
            for season in self.seasons_dict[test_series.pk]
        ) - 0.01

        self.query_dict_1['progress_lte'] = ratio

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.get(
            reverse('seasonmodel-list', args=(test_series.pk,)) +
            '?' + self.query_dict_1.urlencode(),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            len(response.data['results']),
            self.seasons_dict[test_series.pk]
        )
        self.assertTrue(
            all(
                season['last_watched_episode']/season['number_of_episodes'] <= ratio
                for season in response.data['results']
            ))




