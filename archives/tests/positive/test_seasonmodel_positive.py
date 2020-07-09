import datetime
import unittest
from unittest.mock import patch, Mock
from django.test import tag
from django.utils import timezone
from psycopg2.extras import DateRange
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SeasonModelPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Test whether or not it is possible to successfully create 'SeasonModel' instance providing that
    proper set of data is supplied.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.series = initial_data.create_tvseries(users=cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.new_season_data = dict(
            series=cls.series_1,
            season_number=10,
            number_of_episodes=5,
            translation_years=DateRange(
                cls.series_1.translation_years.upper - datetime.timedelta(days=10),
                cls.series_1.translation_years.upper - datetime.timedelta(days=5),
            ))

    def setUp(self) -> None:
        need_to_skip = self.skip_setup_if_tagged()

        if not need_to_skip:
            self.seasons = initial_data.create_seasons(series=self.series)
            self.season_1, *tail = self.seasons

    @tag('skip_setup')
    def test_create_new_season(self):
        """
        Check successful model instance creation. All nullable fields are Null.
        """
        season = archives.models.SeasonModel(**self.new_season_data)
        season.save()

        self.assertTrue(
            archives.models.SeasonModel.objects.filter(**self.new_season_data).exists()
        )

    @unittest.expectedFailure
    def test_fill_nullable_fields(self):
        """
        Check whether or not nullable fields can hold values and  model instance can be saved afterwards.
        """
        self.season_1.last_watched_episode = 3
        self.season_1.episodes = {2: timezone.now()}

        with self.assertRaises(Exception, ):
            self.season_1.full_clean()
            self.season_1.save()

    def test_save_correct_dict_in_episodes(self):
        """
        Check whether or not it is possible to save correct data in 'episodes'field.
        """
        data = {
            2: self.season_1.translation_years.lower + datetime.timedelta(days=1),
            3: self.season_1.translation_years.lower + datetime.timedelta(days=3),
        }
        self.season_1.episodes = data
        self.season_1.save()
        self.season_1.refresh_from_db()

        self.assertDictEqual(
            data,
            self.season_1.episodes
        )

    def test_str(self):
        """
        Check correct string representation of the model instance.
        """
        expected_str = f'pk - {self.season_1.pk},' \
                       f' season number - {self.season_1.season_number},' \
                       f' series name - {self.season_1.series.name}'

        self.assertEqual(
            self.season_1.__str__(),
            expected_str
        )

    def test_is_fully_watched_property(self):
        """
        Check if  'is_fully_watched' property returns True if 'last_watched_episode' field
         is equal to 'number_of_episodes' field.
        """
        self.season_1.last_watched_episode = self.season_1.number_of_episodes

        self.assertTrue(
            self.season_1.is_fully_watched
        )

    def test_is_finished_property(self):
        """
        Check whether or not 'is_finished' property works correctly.
        """
        now = datetime.date.today()
        dater_range_finished = DateRange(
            datetime.date(1999, 9, 1),
            now - datetime.timedelta(days=10)
        )
        dater_range_not_finished = DateRange(
            now - datetime.timedelta(days=10),
            now + datetime.timedelta(days=10)
        )

        self.season_1.translation_years = dater_range_finished

        self.assertTrue(
            self.season_1.is_finished
        )

        self.season_1.translation_years = dater_range_not_finished

        self.assertFalse(
            self.season_1.is_finished
        )

    @tag('skip_setup')
    def test_season_available_range(self):
        """
        Check 'season_available_range' returns available free range for a season.
        """
        initial_data.create_seasons(series=self.series, num_episodes=6)
        adjacent_seasons = archives.models.SeasonModel.objects.filter(
            season_number__in=(3, 4, 5),
        ).order_by('season_number').distinct('season_number')
        previous_season, target_season, next_season = adjacent_seasons

        free_range = target_season.season_available_range

        self.assertTrue(
            previous_season.translation_years < free_range < next_season.translation_years
        )

    def test_new_episode_this_week_property(self):
        """
        Check that 'new_episode_this_week' returns date of the episode if it takes place this week.
        """
        fake_now = datetime.date.fromisocalendar(2020, 28, 3)
        fake_episode_date = fake_now + datetime.timedelta(days=1)
        self.season_1.episodes = {1: fake_episode_date}

        date_mock = Mock(wraps=datetime.date)
        date_mock.today.return_value = fake_now

        with patch('datetime.date', new=date_mock):
            self.assertEqual(
                self.season_1.new_episode_this_week[0],
                fake_episode_date
            )
