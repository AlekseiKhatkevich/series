from rest_framework.test import APITestCase

from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import transaction

from users.helpers import create_test_users
from ..data import initial_data


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
                self.series_1.save()

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
                self.series_1.save()

        self.series_1.refresh_from_db()

        self.assertURLEqual(self.series_1.imdb_url, original_url)


