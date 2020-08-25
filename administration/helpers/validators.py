import ipaddress

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from series import error_codes


@deconstructible
class ValidateIpAddressOrNetwork:
    """
    Validates ip4 or ip6 plain address or network.
    Has possibility to limit min amount of bit in network.
    For example to 24, so 127.0.0/26 is allowed, but 127.0.0/18 is not.
    """

    def __init__(self, min_bit: int) -> None:
        self.min_bit = min_bit
        assert 1 <= self.min_bit <= 32, 'min_bit should be INTEGER in range 1 to 32.'
        assert isinstance(self.min_bit, int), 'min_bit should be INTEGER.'

    def __call__(self, value: str, *args, **kwargs) -> None:
        try:
            ipaddress.ip_network(value)
        except ValueError as err:
            raise ValidationError(
                getattr(err, 'message', str(err))
            )from err

        try:
            net_bit = int(value.split('/')[-1])
        except ValueError:
            pass
        else:
            if net_bit < self.min_bit:
                raise ValidationError(
                    *error_codes.NET_BIT_LOWER
                )


