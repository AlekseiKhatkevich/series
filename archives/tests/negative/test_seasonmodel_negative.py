from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction


class SeasonModelNegativeTest(APITestCase):
    """
    Test whether or not 'SeasonModel' resists against saving bad data.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.series = initial_data.create_tvseries(users=cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.seasons = initial_data.create_seasons(series=self.series)
        self.season_1_1, self.season_1_2, self.season_2_1, self.season_2_2 = self.seasons

    def test_last_watched_episode_validation(self):
        """
        Check whether on not it is possible  to save None via 'last_watched_episode' field
        without raising exception and in case of real value validate, that it would be gte. 1.
        """
        self.season_1_1.full_clean()

        self.assertIsNone(
            self.season_1_1.last_watched_episode
        )

        self.season_1_1.last_watched_episode = -5
        expected_exception_message = \
            f'value={self.season_1_1.last_watched_episode} must be greater or equal 1'

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_episodes_key_validation(self):
        """
        Check whether on not it is possible  to save None via 'episodes' field
        without raising exception and in case of real value validate it.
        """
        self.season_1_1.full_clean()
        self.season_1_1.save()

        self.season_1_1.episodes = {'1': 555, 2: 666, 'XXX': 777, -8: 888}

        with self.assertRaises(ValidationError):
            self.season_1_1.full_clean()

    def test_episodes_timestamp_validation(self):
        """
        Check whether or not it is possible to save incorrect timestamp via field 'episodes'.
        """
        self.season_1_1.episodes = {"1": 'not-a-timestamp'}

        with self.assertRaises(ValidationError):
            self.season_1_1.full_clean()

    def test_last_watched_episode_and_number_of_episodes_are_gte_one_constraint(self):
        """
        Check that DB constrain resists against saving in DB 'last_watched_episode' < 1 if not None and
        'number_of_episodes' < 1
        """
        expected_constraint_code = 'last_watched_episode_and_number_of_episodes_are_gte_one'

        # Constraint should allow to save none to 'last_watched_episode'
        self.season_1_1.save()

        # 1)When 'last_watched_episode' < 1 constraint should raise exception.
        # 2)When 'number_of_episodes' < 1 constraint should raise exception

        for field in ('last_watched_episode', 'number_of_episodes'):
            with self.subTest(field=field):
                with transaction.atomic():
                    with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                        setattr(self.season_1_1, field, 0)
                        self.season_1_1.save()

                self.season_1_1.refresh_from_db()

                self.assertNotEqual(
                    getattr(self.season_1_1, field),
                    0
                )

    def test_mutual_watched_episode_and_number_of_episodes_check_constraint(self):
        """
        Check whether or not  models entries where last watched episode > number of episodes
        can be saved in DB. Constraint should resist against this configuration.
        """
        expected_constraint_code = 'mutual_watched_episode_and_number_of_episodes_check'
        self.season_1_1.last_watched_episode = 99

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                self.season_1_1.save()

        self.season_1_1.refresh_from_db()

        self.assertNotEqual(
            self.season_1_1.last_watched_episode,
            6
        )

    def test_season_number_gte_1_check_constraint(self):
        """
        Check that constraint doesnt allow to save season number < 1.
        """
        expected_constraint_code = 'season_number_gte_1_check'
        self.season_1_1.season_number = 0

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                self.season_1_1.save()

        self.season_1_1.refresh_from_db()

        self.assertNotEqual(
            self.season_1_1.last_watched_episode,
            0
        )

    def test_last_watched_episode_number_is_bigger_then_number_of_episodes_in_season(self):
        """
        Check whether or not model 'clean' method raises exception if
        last_watched_episode number is bigger then number of episodes in season
        """

        self.season_1_1.last_watched_episode = 99
        expected_exception_message = f'Last watched episode number {self.season_1_1.last_watched_episode}' \
                                     f' is greater then number of episodes {self.season_1_1.number_of_episodes}' \
                                     f' in the whole season!!!'

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_key_in_json_gte_num_episodes(self):
        """
        Check whether or not model 'clean' method raises exception if
        we have a key in JSON data in episodes field with number greater
        then number of episodes in season.
        """
        self.season_1_1.episodes = {99: 1588596739.336106}
        expected_exception_message = f'Episode number 99 in "episodes"  field is greater then' \
                                     f' number of episodes {self.season_1_1.number_of_episodes}'

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()
