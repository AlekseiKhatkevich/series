import datetime
import itertools
from typing import BinaryIO, Iterable, Iterator, Optional, Sequence, Union

import PIL
import imagehash
from psycopg2.extras import DateRange
from django.core.files.base import File

test_list = ['a', 1, 2, 99, -8, 2.2, 'sfsdfdf', '6', '88', '5.6', '-67']


def filter_positive_int_or_digit(container: Iterable, to_integer: bool = True) -> Iterator[Union[int, str]]:
    """
    Filters out all str or int gte = 1 from list of mixed iterable data.
    Returns generator with legit data coerced to int.
    """
    _container = tuple(container)
    #  Filters out all positive integers >= 1.
    positive_integers = filter(
        lambda x: isinstance(x, int) and x >= 1,
        _container
    )
    #  Filters out all in positive digits in str.
    positive_string_digits = filter(
        lambda x: isinstance(x, str) and x.isdigit(),
        _container
    )
    #  Combine 2 generators in one.
    final_list_of_positive_numbers_gte_zero = itertools.chain(
        positive_string_digits,
        positive_integers
    )
    #  Coerce all number to int if needed.
    if to_integer:
        final_list_of_positive_numbers_gte_zero = map(
            int,
            final_list_of_positive_numbers_gte_zero
        )
    return final_list_of_positive_numbers_gte_zero


def create_image_hash(
        image: Union[BinaryIO, File],
        raise_errors: bool = False,
) -> Optional[imagehash.ImageHash]:
    """
    Creates image hash on image file.
    """
    try:
        image_hash = imagehash.average_hash(PIL.Image.open(image))
    except PIL.UnidentifiedImageError as err:
        if raise_errors:
            raise err from err
        return None
    return image_hash


def daterange(lower_bound: Optional[Sequence[int]], upper_bound: Optional[Sequence[int]]) -> DateRange:
    """
    Constructs DateRange objects from tuples like (2012, 6, 7) or None.
    """
    for bound in (lower_bound, upper_bound):
        if bound is not None:
            assert len(bound) == 3, 'Year, month and data should be provided mandatory.'

    lower = datetime.date(*lower_bound) if lower_bound is not None else None
    upper = datetime.date(*upper_bound) if upper_bound is not None else None

    return DateRange(lower, upper)


