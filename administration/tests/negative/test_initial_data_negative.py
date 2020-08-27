from rest_framework.test import APISimpleTestCase

from administration.helpers.initial_data import generate_blacklist_ips


class InitialDataNegativeTest(APISimpleTestCase):
    """
    Negative tests on 'administration' app data generators.
    """
    maxDiff = None

    def test_generate_blacklist_ips_assertions(self):
        """
        Check that function 'generate_blacklist_ips' raises assertion error
        on a few predefined occasions.
        """
        kwargs_tuple = (
            dict(num_entries=10, num_active=11, protocols=(4, ), num_networks=0),
            dict(num_entries=10, num_active=9, protocols=(), num_networks=0),
            dict(num_entries=10, num_active=9, protocols=(4, ), num_networks=-1),
            dict(num_entries=10, num_active=9, protocols=(4, 5, 6), num_networks=0),
        )
        exception_messages_tuple = (
            'Amount of entries should be gte than amount of active entries.',
            'Specify at least one address protocol.',
            'Specify positive integer for number of networks to create.',
            'Choose protocol version 4 or 6.',
        )

        for kwargs, exc_msg in zip(kwargs_tuple, exception_messages_tuple):
            with self.subTest(kwargs=kwargs, exc_msg=exc_msg):
                with self.assertRaisesMessage(AssertionError, exc_msg):
                    generate_blacklist_ips(**kwargs)

