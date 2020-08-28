from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

import administration.models
from series import error_codes


class IpBlackListModelNegativeTest(APITestCase):
    """
    Negative tests on 'IpBlacklist' model.
    """
    maxDiff = None

    def setUp(self):
        self.data = dict(
            ip='130.0.0.1',
            stretch=timezone.timedelta(days=1),
        )

    def test_stretch_validation(self):
        """
        Check that negative value can't be saved in 'stretch' field.
        """
        expected_error_message = error_codes.STRETCH_NOT_NEGATIVE.message

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            self.data['stretch'] = timezone.timedelta(days=-1)
            administration.models.IpBlacklist.objects.create(**self.data)

    def test_stretch_positive_check_constraint(self):
        """
        Check that 'stretch_positive_check' raises an exception on negative value being
        attempted to save.
        """
        expected_error_message = 'stretch_positive_check'

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.data['stretch'] = timezone.timedelta(days=-1)
            model_entry = administration.models.IpBlacklist(**self.data)
            model_entry.save(fc=False)

    def test_netmask_check_constraint(self):
        """
        Check that 'netmask_check' would not allow us to save nets with net masks lower then 24 bits
        for ipv4 and lower then 120 bits for ipv6.
        """
        expected_error_message = 'netmask_check'

        for net in ('164.243.145.0/23', 'e983:4632:9c33:ae30:a0dc:3237:2773:d60/119'):
            with self.subTest(net=net):
                with self.assertRaisesMessage(IntegrityError, expected_error_message):
                    with transaction.atomic():
                        self.data['ip'] = net
                        entry = administration.models.IpBlacklist(**self.data)
                        entry.save(fc=False)
