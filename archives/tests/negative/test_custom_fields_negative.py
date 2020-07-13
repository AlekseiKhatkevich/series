from rest_framework.test import APISimpleTestCase
from rest_framework import exceptions as drf_exceptions

from archives.helpers import custom_fields
from series import error_codes


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

    def test_FractionField(self):
        """
        Check that 'FractionField' would raise validation error in case wrong input data is provided.
        """
        field_class = custom_fields.FractionField()
        wrong_serialized_data_1 = {
                'numerator': 5,
            }
        wrong_serialized_data_2 = {
            'numerator': 5,
            'denominator': 'test',
        }
        expected_error_message_1 = error_codes.FRACTIONFIELD_WRONG_KEYS.message
        expected_error_message_2 = error_codes.NOT_A_RATIONAL.message

        for data, message in zip(
                (wrong_serialized_data_1, wrong_serialized_data_2),
                (expected_error_message_1, expected_error_message_2)
        ):
            with self.subTest(data=data, message=message):
                with self.assertRaisesMessage(drf_exceptions.ValidationError, message):
                    field_class.run_validation(data)

