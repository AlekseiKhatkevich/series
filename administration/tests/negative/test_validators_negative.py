from django.core.exceptions import ValidationError
from rest_framework.test import APISimpleTestCase

from administration.helpers import validators
from series import error_codes


class ValidatorsNegativeTest(APISimpleTestCase):
    """
    Negative test on validators in 'administration' app.
    """
    maxDiff = None

    def test_min_bit(self):
        """
        Check that if 'min_bit' is out of range 1 to 32, than exception is arisen.
        """
        expected_error_message = 'bits_down should be INTEGER in range 1 to 32.'

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            validators.ValidateIpAddressOrNetwork(50)

    def test_min_bit_is_int(self):
        """
        Check that if not 'min_bit' is integer, than exception is arisen.
        """
        expected_error_message = 'bits_down should be INTEGER.'

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            # noinspection PyTypeChecker
            validators.ValidateIpAddressOrNetwork(22.2)

    def test_wrong_ip_address(self):
        """
        Check that if wrong ip address or ip network is provided, than error is arisen.
        """
        with self.assertRaises(ValidationError):
            validators.ValidateIpAddressOrNetwork(24)('fake_ip')

    def test_lower_mask_bit(self):
        """
        Check that if net mask bit lower than specified in __init__ threshold, than error is arisen.
        """
        expected_error_message = error_codes.NET_BIT_LOWER.message

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            validators.ValidateIpAddressOrNetwork(24)('127.0.0.0/10')