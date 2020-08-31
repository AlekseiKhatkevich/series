from django.db import models
from administration.helpers.validators import ValidateIpAddressOrNetwork


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
        if ':' in value:
            return ValidateIpAddressOrNetwork(8)(value)
        value = value.strip()
        return value

