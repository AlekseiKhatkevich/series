import os

from django.conf import settings
from django.core.files import File
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesFTSPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on Subtitles FTS api endpoint.
    http://127.0.0.1:8000/archives/tvseries/full-text-search/ GET
    """
    maxDiff = None
   # fixtures = ('subtitles.json',)

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.seasons, cls.seasons_dict = initial_data.create_seasons(
            cls.series,
            num_seasons=3,
            return_sorted=True,
        )
        cls.season_1_1, cls.season_1_2, cls.season_1_3, *series_2_seasons = cls.seasons

    def test_api_response(self):
        """
        Check that fts api endpoint works correctly.
        """
        self.client.force_authenticate(user=self.user_3)

        response = self.client.get(
            reverse('full-text-search'),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )