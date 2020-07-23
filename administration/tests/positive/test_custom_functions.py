from unittest.async_case import IsolatedAsyncioTestCase

import administration.custom_functions
from archives.tests.data import initial_data
from users.helpers import create_test_users
import unittest


class CustomFunctionsPositiveTest(IsolatedAsyncioTestCase):
    """
    Positive test on 'Administration' app custom functions.
    """
    maxDiff = None

    def asyncSetUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

    @unittest.skip
    async def test_HandleWrongUrls(self):
        """
        Check that 'HandleWrongUrls' class instance being called sends email to users who is
        in charge for series where invalid urls are found.
        """
        fake_url = 'https://www.imdb.com/fake'
        self.series_1.imdb_url = fake_url
        self.series_1.save()

        expected_result = f'There are {1} series with invalid urls.'

        result = administration.custom_functions.HandleWrongUrls()()

        self.assertEqual(
            expected_result,
            result,
        )


