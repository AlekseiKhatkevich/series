import ipaddress

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from series import error_codes


@deconstructible
class ValidateIpAddressOrNetwork:
    """
    Validates ip4 or ip6 plain address or network.
    Has possibility to limit min amount of bit in network.
    For example if min_bit = 8 , so 127.0.0/26 is allowed, but 127.0.0/18 is not.
    """

    def __init__(self, bits_down: int) -> None:
        self.bits_down = bits_down
        assert 1 <= self.bits_down <= 32, 'bits_down should be INTEGER in range 1 to 32.'
        assert isinstance(self.bits_down, int), 'bits_down should be INTEGER.'

    def __call__(self, value: str, *args, **kwargs) -> None:
        try:
            ip_obj = ipaddress.ip_network(value)
        except ValueError as err:
            raise ValidationError(
                getattr(err, 'message', str(err))
            )from err

        if ip_obj.prefixlen < ip_obj.max_prefixlen - self.bits_down:
            raise ValidationError(
                *error_codes.NET_BIT_LOWER
            )

        return ip_obj.compressed



