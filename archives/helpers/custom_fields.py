import datetime
from collections.abc import Iterable
from fractions import Fraction

import imagehash
from django.contrib.postgres import fields as postgres_fields
from django.core import exceptions
from django.db import models
from rest_framework import serializers


def change_empty_values(kwargs: dict, instance: models.Field) -> None:
    """
    Helper function to change  EMPTY_VALUES of the FIELD class.
    """
    exclude = kwargs.pop(
        'exclude_empty_values', ()
    )
    if not isinstance(exclude, (tuple, list, set, Iterable)):
        raise TypeError(f'{instance.__class__.__name__} "exclude_empty_values" attribute error.'
                        f'{exclude} should belong to containers or generators')

    instance.empty_values = [
        value for value in instance.__class__.empty_values if value not in exclude
    ]


class CustomJSONField(postgres_fields.JSONField):
    """
    If you want to store None, or empty dict in JSON field you need to include it to exclude_empty_values.
    https://stackoverflow.com/questions/55147169/django-admin-jsonfield-default-empty-dict-wont-save-in-admin
    default EMPTY_VALUES = (None, '', [], (), {})
    """

    def __init__(self, *args, **kwargs):
        change_empty_values(kwargs=kwargs, instance=self)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop('exclude_empty_values', None)
        return name, path, args, kwargs


class ExcludeEmptyValuesMixin:
    """
    Allows to store values excluded from default empty values check default EMPTY_VALUES = (None, '', [], (), {})
    in case they specified in exclude_empty_values arguments( in container). This would allow for example store None
    even if blank=False.
    Useful when you use full_clean to activate model level validation and want to avoid errors saying
    'This field cant be blank' and you dont like to use blank=True either
    """

    def __init__(self, *args, **kwargs):
        change_empty_values(kwargs=kwargs, instance=self)
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs.pop('exclude_empty_values', None)
        return name, path, args, kwargs


class CustomPositiveSmallIntegerField(ExcludeEmptyValuesMixin, models.PositiveSmallIntegerField):
    pass


class ImageHashField(models.CharField):
    """
    Field for handling image hash.
    """
    def to_python(self, value):
        """
        Converts string hash representation to hash array.
        """
        return imagehash.hex_to_hash(value) if value is not None else value

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def get_prep_value(self, value):
        """
        Converts hash array to string.
        """
        return str(value) if value is not None else value


class CustomHStoreField(postgres_fields.HStoreField):
    """
    HStoreField that converts integer keys stored as string to actual integers on deserialization.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value

        return {int(k): datetime.date.fromisoformat(v) if v is not None else v for k, v in value.items()}

    def validate(self, value, model_instance):
        for key, val in value.items():
            if not isinstance(val, (str, datetime.date)) and val is not None:
                raise exceptions.ValidationError(
                    self.error_messages['not_a_string'],
                    code='not_a_string',
                    params={'key': key},
                )


class FractionField(serializers.Field):
    """
    Field to serialize/deserialize Fraction instances.
    """

    def to_representation(self, value: Fraction) -> dict:
        return {
            'numerator': value.numerator,
            'denominator': value.denominator,
        }

    def to_internal_value(self, data: dict) -> Fraction:
        return Fraction(
            data['numerator'],
            data['denominator'],
        )





