import itertools
import operator

from rest_framework.test import APITestCase

import users.models as user_models
from users.helpers import create_test_ips, create_test_users


class UserIPPositiveTest(APITestCase):
    """
    Positive test on model 'UserIP'.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def setUp(self) -> None:
        self.ips = create_test_ips.create_ip_entries(self.users)
        key = operator.attrgetter('user_id')
        ips_grouped_by_user_id = itertools.groupby(sorted(self.ips, key=key), key=key)
        # user to list of user's ips mapping
        self.grouped_dict = {user_id: tuple(ips) for user_id, ips in ips_grouped_by_user_id}

    def test__str__(self):
        """
        Check that model entry string representation works correctly.
        """
        sample_ip = self.ips[0]
        expected_str = f'# {sample_ip.pk} -- Ip address of user {sample_ip.user_id} / {sample_ip.user.email}.'

        self.assertEqual(
            sample_ip.__str__(),
            expected_str
        )

    def test_new_ip_in_db_already(self):
        """
        Check case when user has already this ip in DB. Only 'sample_time' field should be overridden
        with new datetime in this instance. No new entries are made.
        """
        test_user = self.user_1
        sample_ip = test_user.user_ip.first().ip
        original_sample_time = test_user.user_ip.first().sample_time

        new_ip_entry = user_models.UserIP.objects.create(
            user=test_user,
            ip=sample_ip
        )
        # Make sure that we still have 3 ip model entries as we tried to record ip that already was
        # in DB beforehand.
        self.assertEqual(
            test_user.user_ip.all().count(),
            len(self.grouped_dict[test_user.pk]),
        )
        # Make sure that entries with same ip aren't duplicated.
        self.assertEqual(
            test_user.user_ip.filter(ip=sample_ip, user=test_user).count(),
            1
        )
        # Make sure that 'sample_time' has been updated.
        self.assertGreater(
            test_user.user_ip.filter(ip=sample_ip, user=test_user).first().sample_time,
            original_sample_time
        )

    def test_new_ip_not_in_db_already_discard_old_ip(self):
        """
        Check that if we trying to write new ip that isn't present in users ips yet,
        this new ip would be writen fully and as number of ip entries can't overstep 3,
        subsequently ip entry with oldest 'sample_time' should be deleted and overall amount
        of entries should remain intact(=3).
        """
        oldest_ip = self.user_2.user_ip.earliest()
        new_ip = user_models.UserIP.objects.create(
            user=self.user_2,
            ip='228.228.228.228',
        )
        #  Check that we still have 3 entries only for the given user.
        self.assertEqual(
            self.user_2.user_ip.all().count(),
            len(self.grouped_dict[self.user_2.pk]),
        )
        self.assertTrue(
            user_models.UserIP.objects.filter(user=new_ip.user, ip=new_ip.ip,).exists()
        )
        # Check that oldest entry were substituted by freshly created one.
        with self.assertRaises(user_models.UserIP.DoesNotExist):
            oldest_ip.refresh_from_db()
