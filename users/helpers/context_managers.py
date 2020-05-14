from numbers import Integral
from typing import ContextManager, NoReturn, Union

from djoser.conf import settings as djoser_settings


# class DjoserSettingOverride:
#     """
#     Context manager to override Djoser settings (monkey patch them) for unittests purpose:
#     """
#     def __init__(self, name: str, value: Union[str, Integral]) -> NoReturn:
#         """
#         :param name: Setting name.
#         :param value: Setting value. Will be overridden in context manager suit.
#         """
#         self._name = name
#         self._value = value
#         self._original_value = getattr(djoser_settings, self._name)
#
#     def __enter__(self) -> ContextManager:
#         setattr(djoser_settings, self._name, self._value)
#         return self
#
#     def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
#         setattr(djoser_settings, self._name, self._original_value)


class DjoserSettingOverride:
    """
    Context manager to override Djoser settings (monkey patch them) for unittests purpose:
    """
    def __init__(self, name: str, value: Union[str, Integral]) -> NoReturn:
        """
        :param name: Setting name.
        :param value: Setting value. Will be overridden in context manager suit.
        """
        self._name = name
        self._value = value
        self._original_value = getattr(djoser_settings, self._name)

    def __enter__(self) -> ContextManager:
        setattr(djoser_settings, self._name, self._value)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        setattr(djoser_settings, self._name, self._original_value)
