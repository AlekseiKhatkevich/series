from types import MappingProxyType

from rest_framework import serializers
import collections.abc
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
                    {field: error_codes.READ_ONLY.message for field in _read_only_fields_in_data},
                    code=error_codes.READ_ONLY.code
                )


class NoneInsteadEmptyMixin:
    """
    Changes [], {}, (), "" in response data to None.
    Fields for this action should be specified in 'none_if_empty' attribute of nested class Meta.
    """
    swap_empty_container = True
    swap_value = None

    test_dict = {
    "pk": 5,
    "entry_author": "Aleksei Khatkevich",
    "name": "Akbar",
    "imdb_url": "https://www.imdb.com/video/vi2867576345?ref_=hm_hp_i_3&listId=ls05318164944",
    "is_finished": False,
    "rating": 5,
    "interrelationship": None,
    "number_of_seasons": 1,
    "number_of_episodes": 9,
    "images": None,
    "allowed_redactors": [{
        "master": None,
        "friends": [],
        "slaves": None,
        'test': [(), 2, 3, 'fghgh', [], {}]
    }]
}

    def traverse(self, data, keys_to_swap, empty_container_to_swap):
        list_and_dict = list, dict
        if isinstance(data, dict):
            for k, v in data.items():
                if k in keys_to_swap and isinstance(v, collections.abc.Sized) and not len(v):
                    data[k] = self.swap_value
                elif isinstance(v, list_and_dict):
                    self.traverse(v, keys_to_swap,empty_container_to_swap)
        elif isinstance(data, list):
            for num, i in enumerate(data):
                print('LIST')
                if i in empty_container_to_swap:
                    print('Is not None')
                    data[num] = self.swap_value
                elif isinstance(i, list_and_dict):
                    self.traverse(i, keys_to_swap, empty_container_to_swap)
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        #  Return data if 'none_if_empty' attribute unspecified in Meta.
        try:
            fields_to_swap = self.Meta.none_if_empty
        except AttributeError:
            return data

        if self.swap_empty_container:

            assert not (wrong_fields := set(fields_to_swap).difference(self.fields.keys())), \
                f'Fields {wrong_fields} do not belong to serializer "{self.__class__.__name__}"'

            for field in fields_to_swap:
                if not len(data[field]):
                    data[field] = self.swap_value

        return data
