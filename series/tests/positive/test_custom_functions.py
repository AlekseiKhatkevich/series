from rest_framework.test import APISimpleTestCase

from django.contrib.auth import get_user_model

from series.helpers import custom_functions


class CustomFunctionsPositiveTest(APISimpleTestCase):
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





