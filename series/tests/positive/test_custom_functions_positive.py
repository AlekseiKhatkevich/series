from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from series.helpers import custom_functions


class CustomFunctionsPositiveTest(APITestCase):
    """
    Test for custom functions in series project root.
    """

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
                        'date_joined', 'user_country', 'master', 'deleted'
                                      ))
                self.assertSetEqual(
                    expected_result,
                    result
                )






