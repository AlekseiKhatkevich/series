from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from typing import Iterable, Any, Union, Sized


class ValidateOverTheRange:
    """
    Validates whether key withing the iterable.
    """
    def __init__(self, container: Union[Iterable, Sized], *args, **kwargs):
        self._container = container

    def __call__(self, value: Any) -> None:
        if value not in self._container:
            raise ValidationError(
                f'{value} does not locate in the container container',
                code='wrong_country_code',
            )

