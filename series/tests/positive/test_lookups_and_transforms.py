from django.db import connection
from django.db.models import BooleanField, ExpressionWrapper, Q, F
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from users.helpers import create_test_users


class LookupsAndTransformsPositiveTest(APITestCase):
    """
    Positive test on project's lookups and transforms.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()

        cls.series = initial_data.create_tvseries(users=cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.seasons = initial_data.create_seasons(series=cls.series)
        cls.season_1, *tail = cls.seasons

    def test_check_episodes(self):
        """
        Check that 'CheckEpisodes' transform returns True is episodes are ordered by key adn value
        and False if they are not.
        """
        function = 'check_episodes'

        with connection.cursor() as cursor:
            cursor.execute(f"select exists(select * from pg_proc where proname = '{function}');")
            row = cursor.fetchone()
            [exists] = row

        # Make sure that function exists in DB.
        self.assertTrue(exists)

        queryset = archives.models.SeasonModel.objects.annotate(
            is_ordered=ExpressionWrapper(Q(episodes__check_episodes=True), output_field=BooleanField())
        )

        self.assertTrue(
            all(season.is_ordered for season in queryset)
        )

    def test_ToInteger_transform(self):
        """
        Check that 'ToInteger' transform converts text to integer.
        """
        archives.models.TvSeriesModel.objects.all().update(name=5 + F('pk'))

        self.assertEqual(
        archives.models.TvSeriesModel.objects.filter(name__lte=0).count(),
            len(self.series))




