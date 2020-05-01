from rest_framework.test import APITestCase


from ..data import initial_data
from users.helpers import create_test_users
from ... import models


class CreateInitialDataPositiveTest(APITestCase):
    """
    Test process and result of creating test initial data for 'Archives' app tests.
    """

    def test_create_tvseries(self):
        """
        Check whether otr not series are created after running a script.
        """
        users = create_test_users.create_users()
        series = initial_data.create_tvseries(users=users)

        self.assertEqual(
            models.TvSeriesModel.objects.all().count(),
            len(series)
        )