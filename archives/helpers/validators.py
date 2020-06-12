import datetime
import functools
import imghdr
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from types import MappingProxyType

import rest_framework.status as status_codes
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.utils.deconstruct import deconstructible

from archives.helpers import custom_functions
from series import error_codes
from series.helpers import project_decorators

media_root_full_path_partial = functools.partial(os.path.join, settings.MEDIA_ROOT_FULL_PATH)

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


def validate_dict_key_is_digit(value: [dict, bytes]) -> None:
    """
    Validates whether or not all keys in dict are positive integers but saved as string.
    Use case only for JSON dicts as keys in them stored as strings always, even key is integer
     originally.
    """
    if not value:
        return None

    try:
        value = json.loads(value)
    except (ValueError, TypeError):
        value = MappingProxyType(value)

    right_keys = custom_functions.filter_positive_int_or_digit(value.keys(), to_integer=False)
    wrong_keys = value.keys() - set(right_keys)

    if wrong_keys:
        raise ValidationError(
            f'Dictionary keys {wrong_keys} are not  positive integers!',
            code='invalid',
        )


def validate_timestamp(value: [dict, bytes]) -> None:
    """
    Validates whether or not timestamp has correct format.
    Applicable to dict like structures or JSON.
    """
    # In case of None or empty dict...
    if not value:
        return None

    try:
        value = json.loads(value)
    except (ValueError, TypeError):
        value = MappingProxyType(value)

    wrong_timestamps = {}
    for episode, timestamp in value.items():
        try:
            datetime.datetime.fromtimestamp(timestamp)
        except (OverflowError, OSError, ValueError, TypeError):
            wrong_timestamps.update({episode: timestamp})

    if wrong_timestamps:
        raise ValidationError(
            f'List of wrong timestamps{wrong_timestamps}. Timestamp should have correct format',
            code='invalid',
        )


@deconstructible
@project_decorators.typeassert(_domain=str)
class ValidateUrlDomain:
    """
    Validates that given 2nd level domain is a domain of a validated url. 
    For example domain 'www.imdb.com' and domain
    'https://www.imdb.com/title/tt12162902/?ref_=hm_hp_cap_pri_5'
    are the same.
    """

    def __init__(self, domain: str, *args, **kwargs):
        self._domain = domain

    def __call__(self, value: str, *args, **kwargs) -> None:
        domain_of_the_given_url = urllib.parse.urlparse(value).netloc
        if domain_of_the_given_url != self._domain:
            raise ValidationError(
                f'Please provide url to {self._domain} exactly. Your provided url - {value}',
                code='wrong_url'
            )


@deconstructible
@project_decorators.typeassert(_timeout=int)
class ValidateIfUrlIsAlive:
    """
    Checks whether or not given url is alive by sending HEAD request to resource
     and analyze status code of response.
    """

    def __init__(self, timeout: int):
        self._timeout = timeout

    def __call__(self, value: str, *args, **kwargs) -> None:

        request = urllib.request.Request(value, method='HEAD')

        try:
            response = urllib.request.urlopen(request, timeout=self._timeout)
        except urllib.error.HTTPError as err:
            raise ValidationError(
                f'Url {value} does not exists  -- ({str(err)})',
                code='404'
            ) from err
        except urllib.error.URLError as err:
            raise ValidationError(
                f'Url {value} has wrong format. Please double-check -- ({str(err)}',
                code='url_format_error'
            ) from err
        else:
            status = response.status
            if status != status_codes.HTTP_200_OK:
                raise ValidationError(
                    f'Url {value} is not alive or incorrect',
                    code='resource_head_non_200'
                )


@functools.singledispatch
def validate_is_image(value) -> None:
    """
    Validates whether image file is actually an image file and not just a random file with image-like
    file extension.
    :param value: Path of the file or file-like object.
    :return: None
    """
    raise TypeError(f'This argument type {str(type(value))} is not supported by validator'
                    f'function "validate_is_image"')


@validate_is_image.register(File)
def _(value) -> None:
    result = imghdr.what(value, h=None)

    if not result:
        raise ValidationError(
            *error_codes.NOT_AN_IMAGE
        )


@validate_is_image.register(str)
def _(value) -> None:
    value = os.path.normpath(value)
    path = os.path.normpath(
        media_root_full_path_partial(value)
    )
    result = imghdr.what(path, h=None)

    if not result:
        raise ValidationError(
            *error_codes.NOT_AN_IMAGE
        )
