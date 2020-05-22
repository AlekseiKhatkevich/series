from typing import Any, Iterable, Sized, Union

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from rest_framework import validators

from series import error_codes


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


class UserUniqueValidator(validators.UniqueValidator):
    """
    Clone of standard DRF UniqueValidator. Also raises exception when user with this email
    is soft-deleted.
    """
    def __call__(self, value, serializer_field):
        # Determine the underlying model field name. This may not be the
        # same as the serializer field name if `source=<>` is set.
        field_name = serializer_field.source_attrs[-1]
        # Determine the existing instance, if this is an update operation.
        instance = getattr(serializer_field.parent, 'instance', None)

        queryset = self.queryset
        queryset = self.filter_queryset(value, queryset, field_name)
        queryset = self.exclude_current_instance(queryset, instance)
        if queryset.filter(deleted=True).exists():
            raise ValidationError(*error_codes.USER_SOFT_DELETED)
        if validators.qs_exists(queryset):
            raise ValidationError(self.message, code='unique')