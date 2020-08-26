from django.db.models import F
from django.utils import timezone
from rest_framework.test import APITestCase

import administration.models


class IpBlackListModelPositiveTest(APITestCase):
    """
    Positive tests on 'IpBlacklist' model.
    """
    maxDiff = None

    def setUp(self):
        self.data = dict(
            ip='130.0.0.1',
            record_time=timezone.now(),
            stretch=timezone.timedelta(days=1),
        )
        self.one_ip = administration.models.IpBlacklist.objects.create(**self.data)

    def test_model_creation(self):
        """
        Check that if correct input date is provided, than model can be successfully created.
        """

        self.data['ip'] = '127.0.0.1'

        administration.models.IpBlacklist.objects.create(**self.data)

        self.assertTrue(
            administration.models.IpBlacklist.objects.filter(ip='127.0.0.1').exists()
        )

    def test_str(self):
        """
        Check string representation.
        """
        expected_result = self.one_ip.ip

        self.assertEqual(
            self.one_ip.__str__(),
            expected_result,
        )

    def test_is_active_property(self):
        """
        Check that 'is_active' property returns True if ip is still blacklisted and False otherwise.
        """
        self.assertTrue(
            self.one_ip.is_active
        )

        self.one_ip.record_time = F('record_time') - timezone.timedelta(days=100)
        self.one_ip.save(fc=False)

        self.one_ip.refresh_from_db()

        self.assertFalse(
            self.one_ip.is_active
        )

    def test_stretch_remain_property(self):
        """
        Check that 'stretch_remain' returns time remain for ip to release to freedom.
        """
        # noinspection PyTypeChecker
        self.assertAlmostEqual(
            self.one_ip.stretch_remain(),
            timezone.timedelta(days=1),
            delta=timezone.timedelta(seconds=1)
        )