from django.db import connection
from django.db.models import BooleanField, ExpressionWrapper, Q, F
from rest_framework.test import APITestCase
import datetime
import archives.models
import administration.models
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

        cls.net = administration.models.IpBlacklist.objects.create(
            ip='127.0.0.0/28',
            stretch=datetime.timedelta(days=1),
        )

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
        self.assertIn(
            '(name)::integer',
            archives.models.TvSeriesModel.objects.filter(name__int=10).explain(),
        )

    def test_NetContainedOrEqual_lookup(self):
        """
        Check that 'NetContainedOrEqual' properly uses Postgres SQL operator <<=.
        """
        self.assertTrue(
            administration.models.IpBlacklist.objects.filter(
                ip__net_contained_or_equal='127.0.0.0/27'
            ).exists()
        )

    def test_NetContainsOrEquals_lookup(self):
        """
        Check that 'NetContainsOrEquals' properly uses Postgres SQL operator >>= .
        """
        self.assertTrue(
            administration.models.IpBlacklist.objects.filter(
                ip__net_contains_or_equals='127.0.0.0/30'
            ).exists()
        )

    def test_Family(self):
        """
        Check that 'Family' lookup would return ip address protocol version 4 or 6.
        """
        self.assertEqual(
            administration.models.IpBlacklist.objects.all().values('ip__family',).first()['ip__family'],
            4,
        )

    def test_Masklen(self):
        """
        Check that 'Masklen' lookup would return ip address or network mask bit length.
        """
        self.assertEqual(
            administration.models.IpBlacklist.objects.all().values('ip__masklen',).first()['ip__masklen'],
            28,
        )
