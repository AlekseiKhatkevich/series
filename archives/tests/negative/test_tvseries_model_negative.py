from rest_framework.test import APITestCase

from django.core.exceptions import ValidationError

from users.helpers import create_test_users
import archives.models as archive_models
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
        # 2 types of wrong urls(in domain part and another one in path part) conjures 2 different exceptions.
        wrong_url_1 = 'https://www.imdb.com/no-content-here'
        self.series_1.imdb_url = wrong_url_1

        with self.assertRaises(ValidationError) as cm:
            self.series_1.full_clean()
            self.assertIn(
                cm.exception.error_dict['imdb_url'][0].code,
                ('404', 'url_format_error', 'resource_head_non_200')
            )



