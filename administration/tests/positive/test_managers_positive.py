from rest_framework.test import APITestCase

import administration.models
from administration.helpers import initial_data


class AdministrationManagersPositiveTest(APITestCase):
    """
    Positive tests on managers and querysets in 'administration' app.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.blacklist_ips = initial_data.generate_blacklist_ips(10, 6)

    def test_only_active(self):
        """
        Check that 'only_active' Queryset method returns instances where blacklisting is still
        active.
        """
        self.assertEqual(
            administration.models.IpBlacklist.objects.all().only_active().count(),
            6,
        )