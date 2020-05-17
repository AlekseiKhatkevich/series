import itertools
import operator

from rest_framework.test import APITestCase

from users.helpers import create_test_ips, create_test_users
import users.models as user_models


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
        Check case when user has already this ip in DB. Only 'sample_time field should be overridden
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
            3,
        )
        # Make sure that entries with same ip aren't duplicated.
        self.assertEqual(
            test_user.user_ip.filter(ip=sample_ip, user=test_user).count(),
            1
        )
        # Make sure that 'sample_time' has been updated
        self.assertGreater(
            test_user.user_ip.filter(ip=sample_ip, user=test_user).first().sample_time,
            original_sample_time
        )
