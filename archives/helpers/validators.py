import datetime
import functools
import imghdr
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from types import MappingProxyType
from typing import Optional

import cerberus
import imagehash
import rest_framework.status as status_codes
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import File
from django.utils.deconstruct import deconstructible
from psycopg2.extras import DateRange

from archives.helpers import custom_functions
from series import constants, error_codes
from series.helpers import project_decorators

media_root_full_path_partial = functools.partial(os.path.join, settings.MEDIA_ROOT_FULL_PATH)

test_dict = {'a': 1587902034.039742, 1: 1587902034.039742, 2: 1587902034.039742,
             99: 1587902034.039742, -8: 1587902034.039742, 2.2: 1587902034.039742,
             'sfsdfdf': 1587902034.039742, '6': 1587902034.039742, '88': 1587902034.039742,
             '5.6': 1587902034.039742, '-67': 1587902034.039742}


episode_date_schema = {
    'episode_number': {
        'type': 'integer',
        'min': 1,
        'max': 30,
    },
    'release_date': {
        'type': 'date',
    },
}


@deconstructible
class ValidateDict:
    """
    Validates dictionaries according the schema.
    """
    def __init__(self, schema: dict) -> None:
        super().__init__()
        self.validator = cerberus.Validator(schema, require_all=True)

    def __call__(self, value: dict, *args, **kwargs) -> None:
        _value = tuple({'episode_number': k, 'release_date': v} for k, v in value.items())

        for element in _value:
            is_valid = self.validator.validate(element)
            if not is_valid:
                raise ValidationError(
                    f'value -- {element}, error -- {self.validator.errors}'
                )


def skip_if_none_none_zero_positive_validator(value: Optional[int]) -> None:
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
                code='wrong_url',
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
                f'Url {value} has wrong format. Please double-check -- ({str(err)})',
                code='url_format_error'
            ) from err
        else:
            status = response.status
            if status != status_codes.HTTP_200_OK:
                raise ValidationError(
                    f'Url {value} is not alive or incorrect',
                    code='resource_head_non_200'
                )


@deconstructible
class IsImageValidator:
    """
    Validates whether image file is actually an image file and not just a random file with image-like
    file extension.
    """

    @staticmethod
    @project_decorators.allow_disable_in_tests
    def raise_exception(is_image_file: bool) -> None:
        if not is_image_file:
            raise ValidationError(
                *error_codes.NOT_AN_IMAGE
            )

    @functools.singledispatchmethod
    def __call__(self, value) -> None:
        """
        :param value: Path of the file or file-like object.
        """
        raise TypeError(
            f'This argument type {str(type(value))} is not supported by validator function.'
            f'"validate_is_image"'
        )

    @__call__.register(File)
    def _(self, value: File) -> None:
        is_image_file = imghdr.what(value, h=None)
        self.raise_exception(is_image_file)

    @__call__.register(str)
    def _(self, value: str) -> None:
        value = os.path.normpath(value)
        path = os.path.normpath(
            media_root_full_path_partial(value)
        )
        is_image_file = imghdr.what(path, h=None)
        self.raise_exception(is_image_file)


def validate_image_hash(value: imagehash.ImageHash) -> None:
    """
    Validates image hash.
    """
    if not isinstance(value, imagehash.ImageHash):
        raise ValidationError(
            f'Value {value} is not an ImageHash.',
            'not_an_image_hash',
        )


class DateRangeValidatorDescriptor:
    """
    Descriptor class for 'DateRangeValidator'. Converts datetime to date.
    """

    def __init__(self, storage_name: str):
        self.storage_name = storage_name

    def __set__(self, instance, value):
        assert isinstance(value, datetime.date) or value is None, error_codes.NOT_DATETIME.message

        try:
            instance.__dict__[self.storage_name] = value.date()  # Convert datetime object to date object.
        except AttributeError:
            instance.__dict__[self.storage_name] = value  # Already date object or None, all good.


@deconstructible
class DateRangeValidator:
    """
    Validates DateRange prior to DB validation.
    """
    lower = DateRangeValidatorDescriptor('lower')
    upper = DateRangeValidatorDescriptor('upper')

    def __init__(self, lower_inf_allowed: bool = False, upper_inf_allowed: bool = False) -> None:
        self.lower_inf_allowed = lower_inf_allowed
        self.upper_inf_allowed = upper_inf_allowed

    def __call__(self, value: DateRange, *args, **kwargs) -> None:
        assert isinstance(value, DateRange), f'{type(value)} is not {str(DateRange)}.'

        self.lower = value.lower
        self.upper = value.upper

        current_year = datetime.date.today().year

        allowed_lower_bound = constants.LUMIERE_FIRST_FILM_DATE
        allowed_upper_bound = datetime.date(current_year + 2, 1, 1)

        errors = []

        # Check whether lower or upper bound is open.
        if not self.lower_inf_allowed and value.lower_inf:
            errors.append(
                ValidationError(*error_codes.LOWER_BOUND)
            )
        if not self.upper_inf_allowed and value.upper_inf:
            errors.append(
                ValidationError(*error_codes.UPPER_BOUND)
            )
        if errors:
            raise ValidationError(errors)

        # Check that upper bound gte than lower one.
        if None not in (self.lower, self.upper) and self.lower > self.upper:
            errors.append(
                ValidationError(*error_codes.LOWER_GT_UPPER)
            )
        #  Check that dates range is reasonable historically.
        if self.lower is not None and not (allowed_lower_bound < self.lower < allowed_upper_bound):
            errors.append(
                ValidationError(*error_codes.INCORRECT_LOWER_BOUND)
            )
        if self.upper is not None and self.upper > allowed_upper_bound:
            errors.append(
                ValidationError(*error_codes.INCORRECT_UPPER_BOUND)
            )
        if errors:
            raise ValidationError(errors)
