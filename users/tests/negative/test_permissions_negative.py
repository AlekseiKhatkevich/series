import itertools
import operator

import more_itertools
from rest_framework import generics
from rest_framework.test import APIRequestFactory, APITestCase

import users.permissions
from series import error_codes
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

    def test_no_email_in_request_data(self):
        """
        Check that if email data is not provided in request data, than False is returned.
        """
        permission = users.permissions.UserIPPermission()
        expected_error_message = error_codes.EMAIL_REQUIRED.message
        self.request.user = self.user_1

        self.assertFalse(
            permission.has_permission(self.request, self.view)
        )
        self.assertEqual(
            expected_error_message,
            permission.message,
        )

    def test_request_came_from_random_ip_and_user_is_not_an_admin(self):
        """
        Check that if request comes from an any ip outside 3 ones saved in DB for user and user is not
        an admin, than False is returned.
        """
        permission = users.permissions.UserIPPermission()
        test_user = self.user_3
        test_user.is_staff = False

        #  Generate random ip and make sure it is not in users ips saved in DB.
        random_ip = more_itertools.first_true(
            (create_test_ips.generate_random_ip4() for _ in range(10)),
            pred=lambda ip: ip not in self.grouped_dict[test_user.pk],
        )

        request = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=random_ip,
            REMOTE_ADDR=random_ip,
        )

        request.data = dict()
        request.data['email'] = test_user.email
        request.user = test_user

        self.assertFalse(
            permission.has_permission(request, self.view)
        )

    def test_IsUserMasterPermission(self):
        """
        Check that 'IsUserMasterPermission' returns False in case request user is not a master.
        """
        permission = users.permissions.IsUserMasterPermission()
        test_user = self.user_3
        test_user.slaves.all().delete()

        self.request.user = test_user

        self.assertFalse(
            permission.has_permission(self.request, self.view,)
        )


