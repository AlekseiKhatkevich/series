import json
import unittest
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

from archives.helpers import validators


class validatorsPositiveTest(APISimpleTestCase):
    """
    Positive test on 'archives' app custom validators.
    """

    @ unittest.expectedFailure
    def test_skip_if_none_none_zero_positive_validator(self):
        """
        Check that validator does not raises errors on values >= 1.
        """
        value = 5
        with self.assertRaises(ValidationError):
            validators.skip_if_none_none_zero_positive_validator(value)

    @unittest.expectedFailure
    def test_validate_dict_key_is_digit(self):
        """
        Check that validator allows numbers.
        """
        value = {1: 'test', '2': 'test'}

        for value in (value, json.dumps(value)):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validators.validate_dict_key_is_digit(value)

    @unittest.expectedFailure
    def test_validate_timestamp(self):
        """
        Check that validators allows correct timestamps.
        """
        value = {1: timezone.now(), }

        for value in (value, json.dumps(value)):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    validators.validate_timestamp(value)