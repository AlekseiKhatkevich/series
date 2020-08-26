from django.db import models


class IpAndNetworkField(models.GenericIPAddressField):
    """
    'GenericIPAddressField' with no validators at all.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_validators = []
