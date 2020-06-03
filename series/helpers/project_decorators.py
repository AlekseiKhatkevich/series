from typing import Any, Callable, Optional

from django.utils.decorators import classproperty


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

