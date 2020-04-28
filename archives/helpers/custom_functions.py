import itertools
from typing import Iterator, Union, Sequence, Iterable
from more_itertools import SequenceView

test_list = ['a', 1, 2, 99, -8, 2.2, 'sfsdfdf', '6', '88', '5.6', '-67']


def filter_positive_int_or_digit(container: Iterable, to_integer=True) -> Iterator[Union[int, str]]:
    """
    Filters out all str or int gte = 1 from list of mixed iterable data.
    Returns generator with legit data coerced to int.
    """
    _container = SequenceView(container)
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
