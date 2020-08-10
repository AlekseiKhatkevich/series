import collections.abc
import functools
from types import MappingProxyType
from typing import Container, Optional

from rest_framework import serializers

from series import error_codes


class ConditionalRequiredPerFieldMixin:
    """
    Allows to use serializer methods to allow change field is required or not.
    To do so you need to use method 'is_{field_name}_required' which should return bool.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            method_name = f'is_{field_name}_required'
            if hasattr(self, method_name):
                field.required = getattr(self, method_name)()


#  https://stackoverflow.com/questions/48009349/django-rest-framework-conditionally-required-fields
class ActionRequiredFieldsMixin:
    """Required fields per DRF action
    Example:
    PER_ACTION_REQUIRED_FIELDS = {
        'update': ['notes']
    }
    """
    PER_ACTION_REQUIRED_FIELDS = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.context.get('view'):
            action = self.context['view'].action
            required_fields = (self.PER_ACTION_REQUIRED_FIELDS or {}).get(action)
            if required_fields:
                for field_name in required_fields:
                    self.fields[field_name].required = True


class RequiredTogetherFieldsMixin:
    """
    Allow to specify few fields as required together. They are not required until at leas one field from
    this set is filled with data. That would trigger all other fields specified in 'required_together_fields'
    became required. That is ine can leave all required together fields empty or fill tem all.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #  In case wrong field names are in required_together_fields.
        if not self.fields.keys() >= set(self.required_together_fields):
            raise serializers.ValidationError(
                {'required_together_fields': error_codes.REQUIRED_TOGETHER_WRONG_FIELDS_NAMES.message},
                code=error_codes.REQUIRED_TOGETHER_WRONG_FIELDS_NAMES.code
            )
        #  Check whether or not at least one field from 'required_together_fields' is filled with data.
        try:
            required_fields_in_data = set(self.required_together_fields).intersection(self.initial_data)
        except AttributeError:  # if no initial date in serializer...
            pass
        else:
            if required_fields_in_data:
                for field_name, field in self.fields.items():
                    if field_name in self.required_together_fields:
                        field.required = True

    required_together_fields = ()


class ReadOnlyRaisesException:
    """
    Mixin changes standard serializer behaviour when serializer does not raises errors when fields with read only
    attribute set to True are provided in incoming data to opposite behaviour.
    If at leas one of read_only fields in initial data - validation Error is arisen.
    """
    read_only_raises_exception = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.read_only_raises_exception:
            _fields = MappingProxyType(self.fields)
            _read_only_fields = frozenset(field_name for field_name, field in _fields.items() if field.read_only)
            try:
                _initial_data = MappingProxyType(self.initial_data)
                _read_only_fields_in_data = _read_only_fields.intersection(_initial_data)
            except AttributeError:  # if no initial date in serializer...
                pass
            else:
                if _read_only_fields_in_data:
                    raise serializers.ValidationError(
                        {field: error_codes.READ_ONLY_FIELD.message for field in _read_only_fields_in_data},
                        code=error_codes.READ_ONLY_FIELD.code
                    )


class NoneInsteadEmptyMixin:
    """
    Changes [], {}, (), "" in response data to None.
    Fields for this action should be specified in 'none_if_empty' attribute of nested class Meta.
    'none_if_empty' - swaps value of the field if value is empty container.
    'keys_to_swap' - swaps any given key in data if its value is empty.
    'empty_containers_to_swap' - swaps any empty container in data.
    """
    swap_on = True
    swap_value = None
    list_and_dict = (list, dict)

    @functools.singledispatchmethod
    def traverse(
            self,
            data: dict,
            keys_to_swap: Optional[Container],
            empty_containers_to_swap: Optional[Container]
    ) -> None:
        """
        Modifies incoming data recursively by changing:
        a) Values, which keys indicated in 'keys_to_swap' to swap_value, usually None ,
         if value is empty container.
        b) All empty containers, like [], {}, (), etc. if specified in 'empty_containers_to_swap'
        are subject to change as well.
        """
        pass

    @traverse.register(dict)
    def _(self, data, keys_to_swap, empty_containers_to_swap):
        for key, value in data.items():
            # If value is an empty container or string for a specific key.
            if key in keys_to_swap and isinstance(value, collections.abc.Sized) \
                    and not len(value):
                data[key] = self.swap_value
            elif value in empty_containers_to_swap:
                data[key] = self.swap_value
            else:
                self.traverse(value, keys_to_swap, empty_containers_to_swap)

    @traverse.register(list)
    def _(self, data, keys_to_swap, empty_containers_to_swap):
        for num, element in enumerate(data):
            if element in empty_containers_to_swap:
                data[num] = self.swap_value
            else:
                self.traverse(element, keys_to_swap, empty_containers_to_swap)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        #  Return data if 'none_if_empty' attribute unspecified in Meta.

        fields_to_swap = getattr(self.Meta, 'none_if_empty', ())
        keys_to_swap = getattr(self.Meta, 'keys_to_swap', ())
        empty_containers_to_swap = getattr(self.Meta, 'empty_containers_to_swap', ())

        if self.swap_on and any((fields_to_swap, keys_to_swap, empty_containers_to_swap)):

            assert not (wrong_fields := set(fields_to_swap).difference(self.fields.keys())), \
                f'Fields {wrong_fields} do not belong to serializer "{self.__class__.__name__}"'

            for field in fields_to_swap:
                if not len(data[field]):
                    data[field] = self.swap_value

            if keys_to_swap or empty_containers_to_swap:
                self.traverse(data, keys_to_swap, empty_containers_to_swap)

        return data


class ReadOnlyAllFieldsMixin:
    """
    Marks all fields in serializer as 'read_only' fields.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.read_only = True
