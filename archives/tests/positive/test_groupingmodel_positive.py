from rest_framework.test import APITestCase

from users.helpers import create_test_users
from ..data import initial_data


class GroupingModelPositiveTest(APITestCase):
    """
    Tests for GroupingModel.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.series_1, cls.series_2, *tail = initial_data.create_tvseries(users=cls.users)

    def test__str__(self):
        """
        Test whether or not string representation works fine.
        """

        self.series_1.interrelationship.add(
            self.series_2,
            through_defaults={'reason_for_interrelationship': 'No reason'}
        )
        grouping_model_instance = self.series_1.group.get()

        expected_str = f'pk - {grouping_model_instance.pk} /' \
                       f' {grouping_model_instance.from_series.name} /' \
                       f' pk - {grouping_model_instance.from_series_id} <->' \
                       f' {grouping_model_instance.to_series.name} / ' \
                       f'pk - {grouping_model_instance.to_series_id}'

        self.assertEqual(
            self.series_1.interrelationship.get(),
            self.series_2
        )
        self.assertEqual(
            grouping_model_instance.__str__(),
            expected_str
        )

