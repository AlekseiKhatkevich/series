from django.core.exceptions import ValidationError

import datetime
from types import MappingProxyType
import urllib.parse

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
    # In case of None or empty dict...
    try:
        if value < 1:
            raise ValidationError(
                f'{value=} must be greater or equal 1',
                code='min_value',
            )
    except TypeError:
        pass


def validate_dict_key_is_digit(value: dict) -> None:
    """
    Validates whether or not all keys in dict are positive integers but saved as string.
    Use case only for JSON dicts as keys in them stored as strings always, even key is integer
     originally.
    """
    if not value:
        return None

    value = MappingProxyType(value)
    right_keys = custom_functions.filter_positive_int_or_digit(value.keys(), to_integer=False)
    wrong_keys = value.keys() - set(right_keys)

    if wrong_keys:
        raise ValidationError(
            f'Dictionary keys {wrong_keys} are not  positive integers!',
            code='invalid',
        )


def validate_timestamp(value: dict) -> None:
    """
    Validates whether or not timestamp has correct format.
    Applicable to dict like structures or JSON.
    """
    # In case of None or empty dict...
    if not value:
        return None

    value = MappingProxyType(value)
    wrong_timestamps = {}
    for episode, timestamp in value.items():
        try:
            datetime.datetime.fromtimestamp(timestamp)
        except (OverflowError, OSError, ValueError, TypeError) as err:
            wrong_timestamps.update({episode: timestamp})

    if wrong_timestamps:
        raise ValidationError(
            f'List of wrong timestamps{wrong_timestamps}. Timestamp should have correct format',
            code='invalid',
        )


class ValidateUrlDomain:
    """
    Validates that given 2nd level domain is a domain of a validated url. 
    For example domain 'www.imdb.com' and domain
    'https://www.imdb.com/title/tt12162902/?ref_=hm_hp_cap_pri_5'
    are the same.
    """
    def __init__(self, domain: str):
        self._domain = domain

    def __call__(self, value: str):
        domain_of_the_given_url = urllib.parse.urlparse(value).netloc
        if domain_of_the_given_url != self._domain:
            raise ValidationError(
                f'Please provide url to {self._domain} exactly. Your provided url - {value}',
                code='wrong_url'
            )
