import inspect
from typing import Callable, Iterable


def check_code_inside(func: Callable, code: Iterable) -> bool:
    """
    Check whether or not coed snippets(methods, names, etc) inside a callable.
    Use-case: Check if method is overridden.
    """
    source_code = inspect.getsource(func)
    contains_or_not = [snippet for snippet in code if snippet in source_code]
    return bool(contains_or_not)