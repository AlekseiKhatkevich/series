import os

from django.conf import settings
from django.contrib.postgres.search import SearchQuery
from django.db import connection
from django.http import QueryDict
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.models
import archives.serializers
from archives.tests.data import initial_data
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

        test_srt_file_path = os.path.join(settings.MEDIA_ROOT, 'files_for_tests', 'test.srt')
        srt_file = open(test_srt_file_path, 'r')
        data = dict(
            episode_number=1,
            language='en',
            text=srt_file.read(),
            season=cls.season_1_1,
        )
        cls.subtitle = archives.models.Subtitles.objects.create(**data)

    def setUp(self) -> None:
        self.query_dict = QueryDict(mutable=True)

    def test_api_response(self):
        """
        Check that fts api endpoint works correctly.
        """
        search_data = dict(
            search='Harry',
            language='en',
            search_type='plain',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        with CaptureQueriesContext(connection) as ctx:

            response = self.client.get(
                reverse('full-text-search-list') + '?' + self.query_dict.urlencode(),
                data=None,
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )
            self.assertGreaterEqual(
                len(response.data['results']),
                1,
            )
            self.assertSequenceEqual(
                tuple(response.data['results'][0].keys()),
                archives.serializers.FTSSerializer.Meta.fields,
            )
            self.assertTrue(
                any(
                    '"language" = \'en\'' in query['sql'] for query in ctx.captured_queries
                ))
            self.assertEqual(
                response.data['results'][0]['rank'],
                1,
            )

    def test_api_with_no_language(self):
        """
        Check that if no 'language' field is included in request data, than language lookup would be omitted
        in DB query.
        """
        search_data = dict(
            search='Harry',
            search_type='plain',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(
                reverse('full-text-search-list') + '?' + self.query_dict.urlencode(),
                data=None,
                format='json',
            )

            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )
            self.assertFalse(
                any(
                    '"language" = \'en\'' in query['sql'] for query in ctx.captured_queries
                ))

    def test_search_queries_types(self):
        """
        Check that all 4 search queries types are accepted by API endpoint.
        """
        allowed_search_types = SearchQuery.SEARCH_TYPES.keys()
        search_data = dict(
            search='Harry',
            language='en',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        for search_type in allowed_search_types:
            with self.subTest(search_type=search_type):

                self.query_dict['search_type'] = search_type

                response = self.client.get(
                    reverse('full-text-search-list') + '?' + self.query_dict.urlencode(),
                    data=None,
                    format='json',
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )

    def test_detail_headline(self):
        """
        Check that detail api endpoint would show headline of fts.
        """
        search_data = dict(
            search='Harry',
            language='en',
            search_type='plain',
        )
        self.query_dict.update(search_data)

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
                reverse(
                    'full-text-search-detail',
                    args=[self.subtitle.pk],
                ) + '?' + self.query_dict.urlencode(),
                data=None,
                format='json',
            )

        self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
            )
        self.assertIn(
            'Harry',
            response.data['search_headline'],
        )
