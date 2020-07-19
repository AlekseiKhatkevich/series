from django.core import exceptions
from rest_framework.test import APITestCase

import archives.filters
from archives.tests.data import initial_data
from users.helpers import create_test_users


class FiltersNegativeTest(APITestCase):
    """
    Negative test on 'archives' TvseriesModel list view api.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()

    def setUp(self) -> None:
        self.series = initial_data.create_tvseries(users=self.users)
        self.series_1, self.series_2 = self.series

        self.seasons = initial_data.create_seasons(series=self.series)
        self.season_1_1, self.season_1_2, self.season_2_1, self.season_2_2 = self.seasons

    def test_TopBottomPercentField(self):
        """
        Check that 'TopBottomPercentField' field declines positions rather then 'top' and
        bottom and percent outside 1, 99 range. Also should raise error when one of list's element is empty string ''.
        """
        field = archives.filters.TopBottomPercentField()
        data_list_1 = ['test', 10]
        data_list_2 = ['top', - 5]
        data_list_3 = ['top', '']

        for data in (data_list_1, data_list_2, data_list_3):
            with self.subTest(data=data):
                with self.assertRaises(exceptions.ValidationError):
                    field.clean(data)

