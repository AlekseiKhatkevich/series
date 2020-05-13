from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from typing import Iterable, Any, Union, Sized


@deconstructible
class ValidateOverTheRange:
    """
    Validates whether key withing the iterable.
    """
    def __init__(self, container: Union[Iterable, Sized], *args, **kwargs):
        self._container = container

    def __call__(self, value: Any) -> None:
        if value not in self._container:
            raise ValidationError(
                f'{value} does not locate in the container',
                code='not_contains',
            )

