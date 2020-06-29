import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from psycopg2.extras import DateRange
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users


class TvSeriesModelNegativeTest(APITestCase):
    """
    Test for making sure that 'TvSeriesModel' in 'archives' app successfully resists against all
    attempts to put and save bad data in it.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def setUp(self) -> None:
        self.series_1, self.series_2 = initial_data.create_tvseries(users=self.users)

    def test_url_to_imdb_validation_with_non_imdb_url(self):
        """
        Check that sites outside imdb.com can't be validated successfully.
        """
        self.series_1.imdb_url = 'https://stackoverflow.com/'

        with self.assertRaises(ValidationError) as cm:
            self.series_1.full_clean()

        self.assertEqual(
            cm.exception.error_dict['imdb_url'][0].code,
            'wrong_url'
        )

    def test_url_to_imdb_validation_with_non_working_url(self):
        """
        Check that dead url or wrong url to imdb cant be validated.
        """
        # 2 types of wrong urls(in domain part and another one in path part)
        # might conjure up 3 different exceptions.
        wrong_url_1 = 'https://www.imdb.com/no-content-here'
        self.series_1.imdb_url = wrong_url_1

        with self.assertRaises(ValidationError) as cm:
            self.series_1.full_clean()
            self.assertIn(
                cm.exception.error_dict['imdb_url'][0].code,
                ('404', 'url_format_error', 'resource_head_non_200')
            )

    def test_rating_from_1_to_10(self):
        """
        Check that META constraint doesnt allow to save ratings greater then 10.
        """
        self.series_1.rating = 10
        self.series_1.save()

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, 'rating_from_1_to_10'):
                self.series_1.rating = 11
                self.series_1.save(fc=False)

        self.series_1.refresh_from_db()

        self.assertEqual(self.series_1.rating, 10)

    def test_url_to_imdb_check_constraint(self):
        """
        Check that META constraint doesnt allow to save urls not to IMDB.
        """
        original_url = self.series_1.imdb_url

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, 'url_to_imdb_check'):
                self.series_1.imdb_url = 'https://stackoverflow.com/'
                self.series_1.save(fc=False)

        self.series_1.refresh_from_db()

        self.assertURLEqual(self.series_1.imdb_url, original_url)

    def test_translation_years_validator(self):
        """
        Check that translation_years is involved in full_clean.
        """
        translation_years = DateRange(None, datetime.date(2015, 1, 1))
        self.series_1.translation_years = translation_years

        with self.assertRaises(ValidationError):
            self.series_1.save()

    def test_no_medieval_cinema_check(self):
        """
        Check that 'no_medieval_cinema_check' would not allow to save in DB date ranges with:
        a) open lower bound.
        b) lower bound with date earlier then first Lumiere brothers movie.
        """
        expected_error_message = 'no_medieval_cinema_check'
        translation_years_1 = DateRange(None, datetime.date(2015, 1, 1))
        translation_years_2 = DateRange(datetime.date(1815, 1, 1), datetime.date(2015, 1, 1))

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_error_message):
                self.series_1.translation_years = translation_years_1
                self.series_1.save(fc=False)

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.series_1.translation_years = translation_years_2
            self.series_1.save(fc=False)

    def test_defend_future_check(self):
        """
        Check that 'defend_future_check' would not allow to save in DB date ranges with
        upper bound data further in future than 1 of January of the year after following year.
        """
        expected_error_message = 'defend_future_check'
        current_year = datetime.date.today().year
        allowed_upper_bound = datetime.date(current_year + 2, 1, 1)
        translation_years = DateRange(
            datetime.date(2015, 1, 1),
            allowed_upper_bound + datetime.timedelta(days=365)
        )

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.series_1.translation_years = translation_years
            self.series_1.save(fc=False)

