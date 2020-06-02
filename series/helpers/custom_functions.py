import inspect
from typing import Callable, Container, Iterable

from rest_framework.response import Response


def check_code_inside(func: Callable, code: [Container, Iterable]) -> bool:
    """
    Check whether or not coed snippets(methods, names, etc) inside a callable.
    Use-case: Check if method is overridden.
    """
    source_code = inspect.getsource(func)
    contains_or_not = [snippet for snippet in code if snippet in source_code]
    return bool(contains_or_not)


def response_to_dict(response: Response, key_field: str) -> dict:
    """
    Converts DRF response of list view to a nested dictionary  where keys of inner dictionaries
    would be fields specified in key_field
    {
    key_field: {inner nested dict with response.data},
    key_field: {inner nested dict with response.data},
    ...
    }
    """
    return_dict = {}

    # In order to be able to work with paginated and non-paginated responses.
    try:
        data = response.data['results']
    except TypeError:
        data = response.data

    for obj in data:
        try:
            inner_dict = {obj[key_field]: obj}
            return_dict.update(inner_dict)
        except KeyError as err:
            raise KeyError(f'There is no field with name{key_field} in response.data objects') from err

    return return_dict


def key_field_to_field_dict(response: Response, key_field: str, other_field: str) -> dict:
    """
    Returns mapping of {key_field: other_field} based on response.data.
    """
    response_dict = response_to_dict(response, key_field)

    try:
        return_dict = {
            key_field: nested_dict[other_field] for key_field, nested_dict in response_dict.items()
        }
    except KeyError as err:
        raise KeyError(f'There is no field with name{other_field} in response.data objects') from err

    return return_dict


def dict_from_names(*variable_names: str, namespace: Callable = globals) -> dict:
    """
    Returns a dict constructed from variables and their values.
    a = 1
    b = 2
    c = 3
    dict_from_names('a', 'b', 'c') -> {'a': 1, 'b': 2, 'c': 3}
    """
    namespace = namespace()
    return {name: namespace[name] for name in variable_names}


