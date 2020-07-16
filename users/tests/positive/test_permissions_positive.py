import itertools
import operator

from rest_framework import generics
from rest_framework.test import APIRequestFactory, APITestCase

import users.permissions
from users.helpers import create_test_ips, create_test_users


class PermissionPositiveTest(APITestCase):
    """
    Positive test on 'users' app custom permissions.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.view = generics.GenericAPIView()

        cls.ips = create_test_ips.create_ip_entries(cls.users)
        key = operator.attrgetter('user_id')
        ips_grouped_by_user_id = itertools.groupby(sorted(cls.ips, key=key), key=key)
        # user to list of user's ips mapping
        cls.grouped_dict = {user_id: tuple(ips) for user_id, ips in ips_grouped_by_user_id}

    def setUp(self) -> None:
        self.request = APIRequestFactory().request()
        self.request.data = dict()

    def test_UserIPPermission_user_has_record(self):
        """
        Check that 'UserIPPermission' returns True if requests that comes from one of
        account owner 3 last recently used ip addresses.
        """
        permission = users.permissions.UserIPPermission()

        test_user = self.user_3
        test_user_ip = self.grouped_dict[test_user.pk][0].ip

        request = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=test_user_ip,
            REMOTE_ADDR=test_user_ip,
        )
        request.data = dict()
        request.data['email'] = test_user.email
        request.user = test_user

        self.assertTrue(
            permission.has_permission(request, self.view)
        )

    def test_UserIPPermission_user_is_admin(self):
        """
        Check that 'UserIPPermission' returns True if requests user is admin (is staff).
        """
        permission = users.permissions.UserIPPermission()

        test_user = self.user_3
        test_user.is_staff = True

        self.request.data['email'] = test_user.email
        self.request.user = test_user

        self.assertTrue(
            permission.has_permission(self.request, self.view)
        )

    def test_UserIPPermission_user_has_no_records_yet(self):
        """
        Check that 'UserIPPermission' returns True if requests user has no ip records in db yet.
        """
        permission = users.permissions.UserIPPermission()

        test_user = self.user_3
        test_user.user_ip.all().delete()

        self.request.data['email'] = test_user.email
        self.request.user = test_user

        self.assertTrue(
            permission.has_permission(self.request, self.view)
        )

    def test_IsUserMasterPermission(self):
        """
        Check that 'IsUserMasterPermission' permission returns True if user is master.
        """
        permission = users.permissions.IsUserMasterPermission()

        master = self.user_1
        slave = self.user_2
        master.slaves.add(slave)

        self.request.user = master

        self.assertTrue(
            permission.has_permission(self.request, self.view)
        )



