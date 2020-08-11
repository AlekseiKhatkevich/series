from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from archives.helpers.custom_functions import daterange
from series.helpers import custom_functions
from users.helpers import create_test_users


class CustomFunctionsPositiveTest(APITestCase):
    """
    Test for custom functions in series project root.
    """
    @classmethod
    def setUpTestData(cls):
        pass

    def test_check_code_inside(self):
        """
        Check 'check_code_inside' function correct work.
        """
        def test_function():
            return ''.join(map(str.upper, 'please make me uppercase!!!'))

        self.assertTrue(
            custom_functions.check_code_inside(code=('map',), func=test_function)
        )
        self.assertFalse(
            custom_functions.check_code_inside(code=('lambda',), func=test_function)
        )

    def test_get_model_fields_subset(self):
        """
        Check whether or not function 'get_model_fields_subset' returns correct set of field names.
        """
        prefix = 'prefix__'
        expected_result = {'prefix__id', 'prefix__email', 'prefix__first_name', 'prefix__last_name'}

        for model in (get_user_model(), 'Users.User'):
            with self.subTest():
                result = custom_functions.get_model_fields_subset(
                    model=model,
                    prefix=prefix,
                    fields_to_remove=(
                        'password', 'last_login', 'is_superuser', 'is_staff', 'is_active',
                        'date_joined', 'user_country', 'master', 'deleted', 'deleted_time',
                                      ))
                self.assertSetEqual(
                    expected_result,
                    result
                )

    def test_available_range(self):
        """
        Check that 'available_range' function works correctly and returns free portions of a
        big range.
        """
        outer_range = daterange((2010, 1, 1), (2010, 1, 20))
        inner_ranges = [
            daterange((2010, 1, 3), (2010, 1, 9)),
            daterange((2010, 1, 6), (2010, 1, 17)),
        ]

        result = custom_functions.available_range(outer_range, *inner_ranges)

        self.assertEqual(
            len(result),
            2
        )

        for result_date_range in result:
            for inner_range in inner_ranges:
                with self.subTest(result_date_range=result_date_range, inner_range=inner_range):
                    self.assertTrue(
                        (inner_range > result_date_range) or (inner_range < result_date_range)
                    )








