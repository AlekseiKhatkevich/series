from django.db import models


class IpAndNetworkField(models.GenericIPAddressField):
    """
    'GenericIPAddressField' with no validators at all.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_validators = []

    def to_python(self, value):
        if value is None:
            return None
        if not isinstance(value, str):
            value = str(value)
            # add validation logic
        value = value.strip()
        return value

