import ipaddress

from rest_framework.test import APITestCase

import administration.models
from administration.helpers.initial_data import generate_blacklist_ips, generate_changelog
from archives.tests.data import initial_data
from users.helpers import create_test_users


class InitialDataPositiveTest(APITestCase):
    """
    Positive tests on 'administration' app data generators.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def test_generate_changelog_one_user(self):
        """
        Check that 'generate_changelog' successfully creates 'EntriesChangeLog' entries with
        'user' field equal to user provided as 'user' function argument.
        """
        entries = generate_changelog(
            instance=self.series_1,
            user=self.user_3,
            num_logs=5,
        )
        self.assertEqual(
            len(entries),
            5,
        )
        self.assertTrue(
            all(isinstance(entry, administration.models.EntriesChangeLog) for entry in entries)
        )
        self.assertSetEqual(
            {entry.user for entry in entries},
            {self.user_3, },
        )
        self.assertSetEqual(
            {entry.operation_type for entry in entries},
            set(administration.models.OperationTypeChoices.values),
        )

    def test_generate_changelog_multiple_users(self):
        """
        Check that 'generate_changelog' successfully creates 'EntriesChangeLog' entries with
        'user' field randomly chosen from users container provided as 'user' function argument.
        """
        entries = generate_changelog(
            instance=self.series_1,
            num_logs=100,
            user=[self.user_1, self.user_2, self.user_3, ],
        )

        self.assertGreater(
            len({entry.user for entry in entries}),
            1,
        )

    def test_generate_blacklist_ips(self):
        """
        Check that 'generate_blacklist_ips'initial data generator creates 'IpBlacklist'
        entries in DB.
        """
        ips = generate_blacklist_ips(10, 6)

        self.assertEqual(
            administration.models.IpBlacklist.objects.all().count(),
            10,
        )
        self.assertEqual(
            administration.models.IpBlacklist.objects.all().only_active().count(),
            6,
        )
        self.assertNotEqual(
            len({entry.stretch for entry in ips}),
            1
        )
        self.assertTrue(
            all(ipaddress.ip_address(ip).version == 4 for ip in ips)
        )

    def test_generate_blacklist_ips_ip4_and_ip6(self):
        """
        Check that 'generate_blacklist_ips' function can generate both ipv6 and ipv4 addresses
        in one go.
        """
        generate_blacklist_ips(10, 6, protocols=(4, 6))
        ips = administration.models.IpBlacklist.objects.all()

        self.assertEqual(
            len(ips),
            20,
        )
        self.assertEqual(
            len([*filter(lambda obj: ipaddress.ip_address(obj).version == 6, ips)]),
            10,
        )

    def test_generate_blacklist_ips_ip4_and_ip6_and_networks(self):
        """
        Check that 'generate_blacklist_ips' function can generate both ipv6 and ipv4 networks
        in one go.
        """
        generate_blacklist_ips(0, 0, protocols=(4, 6), num_networks=3)
        networks = administration.models.IpBlacklist.objects.all()

        self.assertEqual(
            len(networks),
            6,
        )
        self.assertEqual(
            len([*filter(lambda obj: ipaddress.ip_network(obj).version == 6, networks)]),
            3,
        )
