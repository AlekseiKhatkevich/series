from rest_framework.test import APITestCase


from archives.tests.data import initial_data
from users.helpers import create_test_users
from archives import models


class CreateInitialDataPositiveTest(APITestCase):
    """
    Test process and result of creating test initial data for 'Archives' app tests.
    """
    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()

    def test_create_tvseries(self):
        """
        Check whether or not series are created after running a script.
        """

        series = initial_data.create_tvseries(users=self.users)

        self.assertEqual(
            models.TvSeriesModel.objects.all().count(),
            len(series)
        )

    def test_create_seasons(self):
        """
        Check whether or not seasons are created after running a script.
        """
        series = initial_data.create_tvseries(users=self.users)
        seasons = initial_data.create_seasons(series=series)

        self.assertSequenceEqual(
            seasons,
            models.SeasonModel.objects.all()
        )
