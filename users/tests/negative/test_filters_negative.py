from django.core.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

from users.filters import UserOperationsHistoryFilter


class UsersFiltersNegativeTest(APISimpleTestCase):
    """
    Negative test on 'users' app filters.
    """

    def test_PositiveIntegerFilter(self):
        """
        Check tha 'PositiveIntegerFilter' only accepts positive integers.
        """
        with self.assertRaises(ValidationError):
            UserOperationsHistoryFilter().filters['last_x_operations'].field.clean(3.4)

        with self.assertRaises(ValidationError):
            UserOperationsHistoryFilter().filters['last_x_operations'].field.clean(-1)
