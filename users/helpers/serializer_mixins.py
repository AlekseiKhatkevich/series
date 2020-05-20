from types import MappingProxyType

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
