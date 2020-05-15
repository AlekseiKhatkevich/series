from types import MappingProxyType
from typing import Any, ContextManager, NoReturn

from djoser.conf import settings as djoser_settings


class OverrideDjoserSetting:
    """
    Context manager to override Djoser settings (monkey patch them) for unittests purpose.
    """
    def __init__(self, **kwargs: Any) -> NoReturn:
        self._kwargs = MappingProxyType(kwargs)
        self._original_values = {}

        for name in self._kwargs.keys():
            original_value = getattr(djoser_settings, name)
            self._original_values.update(
                {name: original_value}
            )

    def __enter__(self) -> ContextManager:
        for name, value in self._kwargs.items():
            setattr(djoser_settings, name, value)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        for name, value in self._original_values.items():
            setattr(djoser_settings, name, value)


