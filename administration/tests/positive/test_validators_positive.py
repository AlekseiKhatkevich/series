from rest_framework.test import APISimpleTestCase

from administration.helpers import validators


class ValidatorsPositiveTest(APISimpleTestCase):
    """
    Positive test on validators in 'administration' app.
    """
    maxDiff = None

    def test_ValidateIpAddressOrNetwork_test_validate(self):
        """
        Check that 'ValidateIpAddressOrNetwork' validates positively ip4 or ip6 address or
        ip4 or ip6 network.
        """
        validator = validators.ValidateIpAddressOrNetwork(24)

        samples = (
            '127.0.0.1',
            '127.0.0.0/24',
            '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
            '2001:db8::1000/128',
        )
        for addr_or_net in samples:
            with self.subTest(addr_or_net=addr_or_net):
                validator(value=addr_or_net)