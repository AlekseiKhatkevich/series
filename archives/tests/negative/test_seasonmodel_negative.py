import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from psycopg2.extras import DateRange
from rest_framework.test import APITestCase

from archives.helpers import custom_functions
from archives.tests.data import initial_data
from series import error_codes
from users.helpers import create_test_users


class SeasonModelNegativeTest(APITestCase):
    """
    Test whether or not 'SeasonModel' resists against saving bad data.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.series = initial_data.create_tvseries(users=cls.users)
        cls.series_1, cls.series_2 = cls.series
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.seasons = initial_data.create_seasons(series=self.series)
        self.season_1_1, self.season_1_2, self.season_2_1, self.season_2_2 = self.seasons

    def test_last_watched_episode_validation(self):
        """
        Check whether on not it is possible  to save last watched episode less then 1.
        """
        self.season_1_1.last_watched_episode = -5
        expected_exception_message = \
            f'value={self.season_1_1.last_watched_episode} must be greater or equal 1'

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_episodes_key_validation(self):
        """
        Check whether random data can be cleaned.
        """
        self.season_1_1.episodes = {'1': 555, 2: 666, 'XXX': 777, -8: 888}

        with self.assertRaises(ValidationError):
            self.season_1_1.full_clean()

    def test_episodes_date_validation(self):
        """
        Check whether or not it is possible to save incorrect date via field 'episodes'.
        """
        self.season_1_1.episodes = {1: 'not-a-date'}

        with self.assertRaises(ValidationError):
            self.season_1_1.full_clean()

    def test_last_watched_episode_and_number_of_episodes_are_gte_one_constraint(self):
        """
        Check that DB constrain resists against saving in DB 'last_watched_episode' < 1 if not None and
        30 > 'number_of_episodes' < 1
        """
        expected_constraint_code = 'last_watched_episode_and_number_of_episodes_are_gte_one'

        # 1) When 'last_watched_episode' < 1 constraint should raise exception.
        # 2) When 'number_of_episodes' < 1 constraint should raise exception.
        # 3) When  'number_of_episodes' > 30 constraint should raise exception.

        for field in ('last_watched_episode', 'number_of_episodes'):
            with self.subTest(field=field):
                with transaction.atomic():
                    with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                        setattr(self.season_1_1, field, 0)
                        self.season_1_1.save(fc=False)

                self.season_1_1.refresh_from_db()

                self.assertNotEqual(
                    getattr(self.season_1_1, field),
                    0
                )

        with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
            self.season_1_1.number_of_episodes = 31
            self.season_1_1.save(fc=False)

    def test_mutual_watched_episode_and_number_of_episodes_check_constraint(self):
        """
        Check whether or not  models entries where last watched episode > number of episodes
        can be saved in DB. Constraint should resist against this configuration.
        """
        expected_constraint_code = 'mutual_watched_episode_and_number_of_episodes_check'
        self.season_1_1.last_watched_episode = 29

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                self.season_1_1.save(fc=False)

    def test_season_number_gte_1_check_constraint(self):
        """
        Check that constraint doesnt allow to save season number < 1 and > 30.
        """
        expected_constraint_code = 'season_number_gte_1_check'

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                self.season_1_1.season_number = 0
                self.season_1_1.save(fc=False)

        with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
            self.season_1_1.season_number = 31
            self.season_1_1.save(fc=False)

    def test_last_watched_episode_number_is_bigger_then_number_of_episodes_in_season(self):
        """
        Check whether or not model 'clean' method raises exception if
        last_watched_episode number is bigger then number of episodes in season
        """

        self.season_1_1.last_watched_episode = 99
        expected_exception_message = error_codes.LAST_WATCHED_GTE_NUM_EPISODES.message

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_key_in_dict_gte_num_episodes(self):
        """
        Check whether or not model 'clean' method raises exception if
        we have a key in dict data in episodes field with number greater
        then number of episodes in season.
        """
        self.season_1_1.episodes = {self.season_1_1.number_of_episodes + 1: datetime.date.today()}
        expected_exception_message = error_codes.MAX_KEY_GT_NUM_EPISODES.message

        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_dates_in_episodes_not_sorted(self):
        """
        Check that if dates in 'episodes' field sorted according the keys number are not gte each
        other in succession, then validation error would be raised.
        """
        expected_exception_message = error_codes.EPISODES_DATES_NOT_SORTED.message
        now = datetime.date.today()
        self.season_1_1.episodes = {
            3: now - datetime.timedelta(days=1),
            1: now,
            6: now + - datetime.timedelta(days=1)
        }
        with self.assertRaisesMessage(ValidationError, expected_exception_message):
            self.season_1_1.full_clean()

    def test_exclude_overlapping_seasons_translation_time_check(self):
        """
        Check that in case translation years of seasons in series overlap, then Integrity error
        would be arisen.
        """
        expected_error_message = 'exclude_overlapping_seasons_translation_time_check'
        date_range_1 = custom_functions.daterange((2015, 3, 1), (2015, 7, 1))
        date_range_2 = custom_functions.daterange((2015, 6, 1), (2016, 1, 1))

        self.season_2_1.translation_years = date_range_1
        self.season_2_1.episodes = None
        self.season_2_1.save(fc=False)

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.season_2_2.translation_years = date_range_2
            self.season_2_2.episodes = None
            self.season_2_2.save(fc=False)

    def test_translation_years_within_series(self):
        """
        Check that if translation years of the season are not contained_by translation years
        of the series, then validation error would be arisen.
        """
        expected_error_message = error_codes.SEASON_NOT_IN_SERIES.message
        self.season_1_1.translation_years = DateRange(
            self.season_1_1.series.translation_years.lower - datetime.timedelta(days=10),
            self.season_1_1.series.translation_years.upper,
        )

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.season_1_1.save()

    def test_seasons_translation_years_overlap(self):
        """
        Check that if translation year of season overlaps with translation year of another season from
        a same series, then validation error would be arisen.
        """
        expected_error_message = error_codes.SEASONS_OVERLAP.message
        self.season_1_2.translation_years = self.season_1_1.translation_years

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.season_1_2.save()

    def test_season_translation_years_not_arranged(self):
        """
        Check that if translation years of season with season number 1 fully greater than
         translation years of season 2, then validation error would be arisen.
        """
        expected_error_message = error_codes.TRANSLATION_YEARS_NOT_ARRANGED.message
        # Season number 1 should have daterange lower then season 2.
        # We construct other way around.
        self.season_1_1.translation_years = custom_functions.daterange((2013, 12, 1), (2013, 12, 30))
        self.season_1_1.episodes = None
        self.season_1_2.translation_years = custom_functions.daterange((2013, 1, 1), (2013, 2, 1))
        self.season_1_2.episodes = None
        self.season_1_1.save()

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.season_1_2.save()

    def test_episodes_not_in_season_range(self):
        """
        Check that all 'episodes' dates  should be within 'translation_years' daterange.
        """
        expected_error_message = error_codes.EPISODES_NOT_IN_RANGE.message
        episodes = {
            1: self.season_2_2.translation_years.lower - datetime.timedelta(days=10),
            2: self.season_2_2.translation_years.lower + datetime.timedelta(days=1)
        }

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.season_2_2.episodes = episodes
            self.season_2_2.save()

    def test_max_range_one_year_constraint(self):
        """
        Check that 'max_range_one_year'constraint does not allow to save seasons with translation
        years range greater than one year.
        """
        expected_error_message = 'max_range_one_year'
        date_range = self.season_1_1.translation_years
        self.season_1_1.translation_years = DateRange(
            date_range.lower,
            date_range.lower + datetime.timedelta(days=400),
        )

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.season_1_1.save(fc=False)

    def test_ty_gt_one_year(self):
        """
        Check that clean() method in model would not allow to save season with translation
        years datetime range greater the one year.
        """
        expected_error_message = error_codes.SEASON_TY_GT_YEAR.message
        self.season_1_2.delete()
        date_range = self.season_1_1.translation_years
        self.season_1_1.translation_years = DateRange(
            date_range.lower,
            date_range.lower + datetime.timedelta(days=400),
        )

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.season_1_1.save()

    def test_max_key_lte_number_of_episodes_constraint(self):
        """
        Check that 'max_key_lte_number_of_episodes' would not allow to save 'episodes' field
        with key greater than 'number_of_episodes.
        """
        expected_error_message = 'max_key_lte_number_of_episodes'
        self.season_1_2.episodes = {
            self.season_1_2.number_of_episodes + 1:
                self.season_1_2.season_available_range.lower + datetime.timedelta(days=1)
        }

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.season_1_2.save(fc=False)

    def test_episodes_within_season_check(self):
        """
        Check that 'episodes_within_season_check' constraint would not allow to save 'episodes'
        with date out of 'translation-years' range.
        """
        expected_error_message = 'episodes_within_season_check'
        self.season_2_1.episodes = {
            1:
                self.season_2_1.translation_years.upper + datetime.timedelta(days=10)
        }

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.season_2_1.save(fc=False)

    def test_episodes_sequence_check(self):
        """
        Check that 'episodes_sequence_check' constraint would not allow to save episodes
        where keys order does not coincide to values order.
        """
        expected_error_message = 'episodes_sequence_check'

        episodes = self.season_1_1.episodes
        self.season_1_1.episodes = {1: episodes[2], 2: episodes[1]}

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.season_1_1.save(fc=False)


