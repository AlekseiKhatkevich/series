import itertools
import operator

from django.db import models
from django.db.utils import IntegrityError, InternalError
from rest_framework.test import APITestCase

from users.helpers import create_test_ips, create_test_users
from users.models import UserIP


class UserIPNegativeTest(APITestCase):
    """
    Negative test on model 'UserIP'.
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

    def test_max_3_ips_check_constraint(self):
        """
        Check that 'max_3_ips' check constraint would not allow to save more then 3 IP entries
        for each user.
        """
        expected_error_message = 'Cannot insert more than 3 ips for each user.'

        with self.assertRaisesMessage(InternalError, expected_error_message):
            entry = UserIP(ip='228.228.228.228', user=self.user_1)
            models.Model.save(entry)

