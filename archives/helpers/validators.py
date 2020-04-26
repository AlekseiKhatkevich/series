from django.core.exceptions import ValidationError

import datetime

from archives.helpers import custom_functions

test_dict = {'a': 1587902034.039742, 1: 1587902034.039742, 2: 1587902034.039742,
             99: 1587902034.039742, -8: 1587902034.039742, 2.2: 1587902034.039742,
             'sfsdfdf': 1587902034.039742, '6': 1587902034.039742, '88': 1587902034.039742,
             '5.6': 1587902034.039742, '-67': 1587902034.039742}


def skip_if_none_none_zero_positive_validator(value: int) -> None:
    """
    Raises Validation error in case value is les then 1. Skips if value is None.
    Useful when field can hold none as a legit value
    """
    if value is None:
        return None
    elif value < 1:
        raise ValidationError(
            f'{value} must be greater or equal 1'
        )


def validate_dict_key_is_digit(value: dict) -> None:
    """
    Validates whether or not all keys in dict are positive integers but saved as string.
    Use case only for JSON dicts as keys in them stored as strings always, even key is integer
     originally.
    """

    right_keys = custom_functions.filter_positive_int_or_digit(value.keys(), to_integer=False)
    wrong_keys = value.keys() - set(right_keys)

    if wrong_keys:
        raise ValidationError(
            f'Dictionary keys {wrong_keys} are not  positive integers!'
        )


def validate_timestamp(value: dict) -> None:
    """
    Validates whether or not timestamp has correct format.
    Applicable to dict like structures or JSON.
    """
    wrong_timestamps = {}
    for episode, timestamp in value.items():
        try:
            datetime.datetime.fromtimestamp(timestamp)
        except (OverflowError, OSError, ValueError, TypeError) as err:
            wrong_timestamps.update({episode: timestamp})

    if wrong_timestamps:
        raise ValidationError(
            f'List of wrong timestamps{wrong_timestamps}. Timestamp should have correct format'
        )
