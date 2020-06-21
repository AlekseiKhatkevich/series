import json

from django.core.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase
from series import error_codes
from archives.helpers import validators
from archives.tests.data import initial_data


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

    def test_ValidateUrlDomain(self):
        """
        Check that validator would throw exception on  incorrect domain.
        """
        domain = r'https://yandex.ru/'
        expected_domain = r'https://google.com/'
        expected_error_message = \
            f'Please provide url to {expected_domain} exactly. Your provided url - {domain}'
        validator = validators.ValidateUrlDomain(domain=expected_domain)

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(domain)

    def test_ValidateIfUrlIsAlive(self):
        """
        Check that validator raises validation error in case url is corrupted.
        """
        validator = validators.ValidateIfUrlIsAlive(3)

        wrong_url_1 = r'https://www.imdb.com/no-content-here'
        expected_error_message_1 = f'Url {wrong_url_1} does not exists  -- (HTTP Error 404: Not Found)'
        with self.assertRaisesMessage(ValidationError, expected_error_message_1):
            validator(wrong_url_1)

        wrong_url_2 = r'https://yandex.ru1/search/'
        expected_error_message_2 = \
            f'Url {wrong_url_2} has wrong format. Please double-check -- ' \
            f'(<urlopen error [Errno 11001] getaddrinfo failed>)'
        with self.assertRaisesMessage(ValidationError, expected_error_message_2):
            validator(wrong_url_2)

    def test_IsImageValidator(self):
        """
        Check that validator raises exceptions on incorrect images.
        """
        validator = validators.IsImageValidator(switch_off_in_tests=False)
        image_file = initial_data.generate_test_image_old_version()
        expected_error_message = error_codes.NOT_AN_IMAGE.message

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(image_file)

