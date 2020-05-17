from types import MappingProxyType
from typing import Any, ContextManager, NoReturn

from django.db.models.base import ModelBase


class OverrideModelAttributes:
    """
    Context managers to override attributes in model's fields.
    example:
    with context_managers.OverrideModelAttributes(
            model=users_models.UserIP,
            field='sample_time',
            auto_now=False
    ):
    would temporarily turn 'auto_now' to False and then turns it back again to True.
    """
    def __init__(self, model: ModelBase, field: str, **attributes: Any) -> NoReturn:
        self._attributes = MappingProxyType(attributes)
        self._original_attributes = {}
        self._field = model._meta.get_field(field)

        for attr_name in self._attributes.keys():
            original_attr_value = getattr(
                self._field,
                attr_name,
            )
            self._original_attributes.update(
                        {attr_name: original_attr_value}
                    )

    def __enter__(self) -> ContextManager:
        for attr_name, attr_value in self._attributes.items():
            setattr(
                self._field,
                attr_name,
                attr_value,
            )
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        for attr_name, attr_value in self._original_attributes.items():
            setattr(
                self._field,
                attr_name,
                attr_value,
            )


