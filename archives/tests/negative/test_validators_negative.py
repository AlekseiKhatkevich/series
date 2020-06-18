import json

from django.core.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

from archives.helpers import validators


class validatorsNegativeTest(APISimpleTestCase):
    """
    Negative test on 'archives' app custom validators.
    """

    def test_skip_if_none_none_zero_positive_validator(self):
        """
        Check that validator raises error on values < 1 but skips None.
        """
        value = -1
        expected_error_message = f'{value=} must be greater or equal 1'

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validators.skip_if_none_none_zero_positive_validator(value)

        value = None
        validators.skip_if_none_none_zero_positive_validator(value)

    def test_validate_dict_key_is_digit(self):
        """
        Check that validator not allows NANs.
        """
        value = {'wrong_key': 'test', '2': 'test'}
        expected_error_message = f"Dictionary keys {set(('wrong_key', ))} are not  positive integers!"

        for value in (value, json.dumps(value)):
            with self.subTest(value=value):
                with self.assertRaisesMessage(ValidationError, expected_error_message):
                    validators.validate_dict_key_is_digit(value)

    def test_validate_timestamp(self):
        """
        Check that validators raises validation error on incorrect timestamps.
        """
        value = {1: 'wrong_timestamp', }

        for value in (value, json.dumps(value)):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validators.validate_timestamp(value)
