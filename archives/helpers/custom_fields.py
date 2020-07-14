import datetime
import numbers
from collections.abc import Iterable
from fractions import Fraction

import imagehash
from django.contrib.postgres import fields as postgres_fields
from django.core import exceptions
from django.db import models
from rest_framework import serializers

from series import error_codes


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
    Converts ISO date to datetime.date.
    """
    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def validate(self, value, model_instance):
        return models.Field.validate(self, value, model_instance)
        # for key, val in value.items():
        #     if not isinstance(key, int) and key is not None:
        #         raise exceptions.ValidationError(
        #             *error_codes.KEY_NOT_AN_INTEGER,
        #         )
        #     if not isinstance(val, datetime.date) and val is not None:
        #         raise exceptions.ValidationError(
        #             *error_codes.NOT_ISO_DATE,
        #         )

    def to_python(self, value):
        if value is None:
            return value

        converted_data = {}

        for number, date in value.items():
            if isinstance(number, str) and isinstance(date, str):
                try:
                    number = int(number)
                except ValueError:
                    raise exceptions.ValidationError(
                        *error_codes.KEY_NOT_AN_INTEGER,
                    )
                try:
                    date = datetime.date.fromisoformat(date)
                except ValueError:
                    raise exceptions.ValidationError(
                        *error_codes.NOT_ISO_DATE,
                    )

                converted_data.update({int(number): date})

        return converted_data or super().to_python(value)


class FractionField(serializers.Field):
    """
    Field to serialize/deserialize Fraction instances.
    """

    def to_representation(self, value: Fraction) -> dict:
        assert isinstance(value, Fraction), 'Value should be instance of Fraction.'

        return {
            'numerator': value.numerator,
            'denominator': value.denominator,
        }

    def to_internal_value(self, data: dict) -> Fraction:
        return Fraction(
            data['numerator'],
            data['denominator'],
        )

    def run_validation(self, data=serializers.empty):
        self.error_messages = {
            err.code: err.message for err in (
                error_codes.NOT_A_RATIONAL,
                error_codes.FRACTIONFIELD_WRONG_KEYS,
            )}

        (is_empty_value, data) = self.validate_empty_values(data)
        if is_empty_value:
            return data

        try:
            numerator = data['numerator']
            denominator = data['denominator']
        except (KeyError, TypeError):
            self.fail(
                error_codes.FRACTIONFIELD_WRONG_KEYS.code
            )

        for number in (numerator, denominator):
            if not isinstance(number, numbers.Rational):
                self.fail(
                    error_codes.NOT_A_RATIONAL.code
                )

        value = self.to_internal_value(data)
        self.run_validators(value)

        return value







