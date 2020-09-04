import functools
from typing import Any, Callable, Optional

from django.conf import settings
from django.core.cache import cache


class Typed:
    """
    Descriptor for a type-checked attribute.
    """
    def __init__(self, name: str, expected_type: type) -> None:
        self.name = name
        self.expected_type = expected_type

    def __get__(self, instance: object, owner: type) -> Optional[Any]:
        if instance is None:
            return self
        else:
            try:
                return instance.__dict__[self.name]
            except KeyError as err:
                raise AttributeError(
                    f'{owner.__name__} object has no attribute {self.name}'
                ) from err

    def __set__(self, instance: object, value: Any) -> None:
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f'Expected type {str(self.expected_type)}. Instead have gotten type {str(type(value))}'
            )
        instance.__dict__[self.name] = value

    def __delete__(self, instance: object) -> None:
        del instance.__dict__[self.name]


def typeassert(**kwargs: type) -> Callable:
    """
    Class decorator to check whether init attributes have proper type.
    Example:
    @project_decorators.typeassert(_domain=str)
    class ValidateUrlDomain:
        def __init__(self, domain: str, *args, **kwargs):
            self._domain = domain

    Please do understand that it checks arguments setting in init during self.xxx = xxx operation, that is
    if you use leading underscore , like self._xxx = xxx, then you need to specify exactly _xxx in decorator.
    """
    def decorate(cls: type) -> type:
        for name, expected_type in kwargs.items():
            setattr(cls, name, Typed(name, expected_type))
        return cls
    return decorate


def allow_disable_in_tests(func):
    """
    Gives a chosen validator possibility to be switched off in tests.
     In test fixture decorator '@test_helpers.switch_off_validator' should be used as well.
     Doesnt work with @method_decorator.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # https://stackoverflow.com/questions/62470603/
        # get-function-or-class-method-name-from-inside-decorator-in-python
        try:
            version = func.__func__.__qualname__.split('.')[0]  # to support @classmethod.
        except AttributeError:
            version = func.__qualname__.split('.')[0]  # bound methods, static methods and plain functions.

        key = dict(key='switch_off_in_tests', version=version)
        need_to_switch_off_in_tests = cache.get(**key, default=False)
        cache.delete(**key)

        if settings.IM_IN_TEST_MODE and need_to_switch_off_in_tests:
            return None

        value = func(*args, **kwargs)

        return value

    return wrapper


def profiler(func):
    """
    Counts number of calls to a function.
    """
    ncalls = 0

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal ncalls
        ncalls += 1
        return func(*args, **kwargs)
    wrapper.ncalls = lambda: ncalls
    return wrapper


