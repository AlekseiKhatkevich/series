from collections.abc import Iterable
import imagehash
from archives.helpers import validators as custom_validators
from django.contrib.postgres import fields as postgres_fields
from django.db import models


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

    def __init__(self, verbose_name=None, name=None, encoder=None, **kwargs):
        change_empty_values(kwargs=kwargs, instance=self)
        super().__init__(verbose_name, name, encoder, **kwargs)

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

    def __init__(self, verbose_name=None, name=None, primary_key=False, max_length=None, unique=False, blank=False,
                 null=False, db_index=False, rel=None, default=models.fields.NOT_PROVIDED, editable=True,
                 serialize=True,
                 unique_for_date=None, unique_for_month=None, unique_for_year=None, choices=None, help_text='',
                 db_column=None, db_tablespace=None, auto_created=False, validators=(), error_messages=None, **kwargs):

        change_empty_values(kwargs=kwargs, instance=self)

        super().__init__(verbose_name, name, primary_key, max_length, unique, blank, null, db_index, rel, default,
                         editable, serialize, unique_for_date, unique_for_month, unique_for_year, choices, help_text,
                         db_column, db_tablespace, auto_created, validators, error_messages, )

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


