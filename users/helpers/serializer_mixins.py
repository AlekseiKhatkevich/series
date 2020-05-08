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
