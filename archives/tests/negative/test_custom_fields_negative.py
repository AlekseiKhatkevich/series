from rest_framework.test import APISimpleTestCase

from archives.helpers import custom_fields


class CustomFieldsNegativeTest(APISimpleTestCase):
    """
    Test how custom fields resist against putting wrong type of data in
    "exclude_empty_values" attribute.
    """

    def test_wrong_exclude_empty_values_custom_JSON_field(self):
        """
        Check whether or nor Type error with specific message would be conjured up in case
        wrong type of "exclude_empty_values" attribute would be passed in the constructor
        in a haphazard way.
        """
        wrong_value = 1
        expected_error_message = f'{custom_fields.CustomJSONField.__name__} ' \
                                 f'"exclude_empty_values" attribute error.'f'{wrong_value}' \
                                 f' should belong to containers or generators'
        with self.assertRaisesMessage(TypeError, expected_error_message):
            custom_fields.CustomJSONField(exclude_empty_values=wrong_value)

    def test_wrong_exclude_empty_values_custom_PositiveSmallIntegerField_field(self):
        """
        Same as above but for PositiveSmallIntegerField .
        """
        wrong_value = 1
        expected_error_message = f'{custom_fields.CustomPositiveSmallIntegerField.__name__} ' \
                                 f'"exclude_empty_values" attribute error.'f'{wrong_value}' \
                                 f' should belong to containers or generators'
        with self.assertRaisesMessage(TypeError, expected_error_message):
            custom_fields.CustomPositiveSmallIntegerField(exclude_empty_values=wrong_value)
