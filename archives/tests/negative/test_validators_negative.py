import datetime
import json

from django.core.exceptions import ValidationError
from psycopg2.extras import DateRange
from rest_framework.test import APISimpleTestCase

from archives.helpers import validators
from archives.tests.data import initial_data
from series import error_codes


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

    def test_DateRangeValidator_with_wrong_value(self):
        """
        Check that if 'DateRangeValidator' receives wrong value type, than assertion error
        would be raised.
        """
        validator = validators.DateRangeValidator()
        value = 10
        expected_error_message = f'{type(value)} is not {str(DateRange)}.'

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            validator(value)

    def test_DateRangeValidator_lower_inf_forbidden(self):
        """
        Check that if 'DateRangeValidator' doe not allow lower bound to be infinite, then if lower
        infinite value is provided, then validation error would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.LOWER_BOUND.message
        range_with_lower_inf = DateRange(None, datetime.date.today())

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(range_with_lower_inf)

    def test_DateRangeValidator_upper_inf_forbidden(self):
        """
        Check that if 'DateRangeValidator' doe not allow upper bound to be infinite, than if upper
        infinite value is provided, then validation error would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.UPPER_BOUND.message
        range_with_upper_inf = DateRange(datetime.date.today(), None)

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(range_with_upper_inf)

    def test_DateRangeValidator_lower_gt_upper(self):
        """
        Check that if 'DateRangeValidator' receives daterange where lower > upper,
        than validation error would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.LOWER_GT_UPPER.message
        range_with_lower_gt_upper = DateRange(datetime.date(2020, 1, 1), datetime.date(2019, 1, 1))

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(range_with_lower_gt_upper)

    def test_DateRangeValidator_lower_under_allowed_lower_bound(self):
        """
        Check that if 'DateRangeValidator' receives daterange where lower > date of the first
        Lumiere brothers movie, than validation error would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.WAY_TO_OLD.message
        range_with_caveman_cinema = DateRange(datetime.date(1820, 1, 1), datetime.date(2019, 1, 1))

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(range_with_caveman_cinema)

    def test_DateRangeValidator_upper_is_above_allowed_upper_bound(self):
        """
        Check that if 'DateRangeValidator' receives daterange where upper > 1 january of the
        next year after following year, than validation error would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.NO_FUTURE.message
        range_with_future = DateRange(datetime.date(2019, 1, 1), datetime.date(3000, 1, 1))

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validator(range_with_future)

    def test_DateRangeValidator_set_bounds_with_wrong_type(self):
        """
        Check that if 'DateRangeValidator' bound(s) of type not datetime.date or None, then validation error
        would be raised.
        """
        validator = validators.DateRangeValidator()
        expected_error_message = error_codes.NOT_DATETIME.message
        range_with_wrong_value = DateRange(datetime.date(2019, 1, 1), 228)

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            validator(range_with_wrong_value)

