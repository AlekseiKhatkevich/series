from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesFTSPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on Subtitles FTS api endpoint.
    /archives/tvseries/full-text-search/ GET
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.seasons, cls.seasons_dict = initial_data.create_seasons(
            cls.series,
            num_seasons=1,
            return_sorted=True,
        )
        cls.season_1_1, *rest = cls.seasons

    def setUp(self) -> None:
        self.query_dict = QueryDict(mutable=True)

    def test_validate_query_params_no_search(self):
        """
        Check that if 'search' was not specified in query parameters, that validation error is arisen.
        Check that if wrong language code was specified in query parameters, that validation error is arisen.
        Check that if wrong search type  was specified in query parameters, that validation error is arisen.
        """
        expected_error_messages = (
            error_codes.NO_SEARCH.message,
            error_codes.WRONG_LANGUAGE_CODE.message,
            error_codes.WRONG_SEARCH_TYPE.message,
        )
        search_data = dict(
            language='xx',
            search_type='xx',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('full-text-search-list') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        for message in expected_error_messages:
            with self.subTest(message=message):
                self.assertIn(
                    message,
                    response.data['query_parameters'],
                )

    def test_search_query_with_only_stopwords(self):
        """
        Check that if no results has been found and search query contains only stop words, than validation
        error would be arisen.
        """
        expected_error_message = error_codes.WRONG_SEARCH_QUERY.message
        search_data = dict(
            language='en',
            search_type='raw',
            search='the',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('full-text-search-list') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_400_BAD_REQUEST,
            field=None,
            error_message=expected_error_message,
        )