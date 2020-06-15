from rest_framework.test import APISimpleTestCase

from archives.helpers import custom_functions


class CustomFunctionsPositiveTest(APISimpleTestCase):
    """
    Tests for custom functions in 'archives' app.
    """

    def test_filter_positive_int_or_digit(self):
        """
        Check whether or not 'filter_positive_int_or_digit' function successfully filters all
        integers >= 1 or str. digits of same nature.
        """
        # all string digits are converted to int.
        result = custom_functions.filter_positive_int_or_digit(custom_functions.test_list)

        for element in result:
            with self.subTest(element=element):
                self.assertIsInstance(element, int)
                self.assertGreaterEqual(element, 1)

        # string digits weren't converted to int. Part of elements are still str. digits >= 1.
        result = custom_functions.filter_positive_int_or_digit(
            custom_functions.test_list, to_integer=False
        )

        self.assertTrue(
            any(
                filter(
                    lambda x: isinstance(x, str) and x.isdigit(),
                    result)
            )
        )

