from rest_framework.test import APITestCase

from django.utils import timezone

from users.helpers import create_test_users
from archives.tests.data import initial_data
import archives.models

import unittest


class SeasonModelPositiveTest(APITestCase):
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
            season_number=1,
            number_of_episodes=5
        )

    def setUp(self) -> None:
        self.seasons = initial_data.create_seasons(series=self.series)
        self.season_1, *tail = self.seasons

    def test_create_new_season(self):
        """
        Check successful model instance creation. All nullable fields are Null.
        """
        archives.models.SeasonModel.objects.create(**self.new_season_data)

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

    def test_str(self):
        """
        Check correct string representation of the model instance.
        """
        expected_str = f'season number - {self.season_1.season_number},' \
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
        # Situation where we dont have information about last episode release datetime.

        self.assertIsNone(
            self.season_1.is_finished
        )

