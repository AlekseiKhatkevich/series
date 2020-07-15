import datetime

from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm
from rest_framework import generics
from rest_framework.test import APIRequestFactory, APITestCase

import archives.permissions
from archives.tests.data import initial_data
from series import constants
from users.helpers import create_test_users


class PermissionPositiveTest(APITestCase):
    """
    Positive test on 'archives' app custom permissions.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.view = generics.GenericAPIView()

    def setUp(self) -> None:
        self.request = APIRequestFactory().request()

    def test_ReadOnlyIfOnlyAuthenticated(self):
        """
        Check that 'ReadOnlyIfOnlyAuthenticated' permission returns True if user is
        authenticated and request method is safe method.
        """
        permission = archives.permissions.ReadOnlyIfOnlyAuthenticated()
        self.request.user = self.user_1

        self.assertTrue(
            permission.has_permission(self.request, self.view)
        )
        self.assertTrue(
            permission.has_object_permission(self.request, self.view, self.series_1)
        )

    def test_IsObjectOwner(self):
        """
        Check that 'IsObjectOwner' returns True if object author is request user.
        """
        permission = archives.permissions.IsObjectOwner()
        obj = self.series_1
        author = obj.entry_author
        self.request.user = author

        self.assertTrue(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_MasterSlaveRelations(self):
        """
        Check that 'MasterSlaveRelations' permission returns True if request user is slave or master of
        object author.
        """
        permission = archives.permissions.MasterSlaveRelations()
        obj = self.series_1
        author = obj.entry_author
        slave = self.series_2.entry_author
        author.slaves.add(slave)
        self.request.user = slave

        self.assertTrue(
            permission.has_object_permission(self.request, self.view, obj)
        )

        self.request.user = author
        obj = self.series_2
        self.assertTrue(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_FriendsGuardianPermission(self):
        """
        Check that 'FriendsGuardianPermission' permission returns True if request user has permission
        'DEFAULT_OBJECT_LEVEL_PERMISSION_CODE' on this object given him by object owner.
        """
        permission = archives.permissions.FriendsGuardianPermission()
        obj = self.series_1
        friend = self.series_2.entry_author
        perm_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE
        assign_perm(perm_code, friend, obj)
        self.request.user = friend

        self.assertTrue(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_HandleDeletedUsersEntriesPermission(self):
        """
        Check that 'HandleDeletedUsersEntriesPermission' permission returns True if object author is soft-deleted
        for at lest half-year and either a) request user is staff or b) request user has special group permission
        to handle entries of-soft deleted users.
        """
        permission = archives.permissions.HandleDeletedUsersEntriesPermission()
        time_fringe = constants.DAYS_ELAPSED_SOFT_DELETED_USER

        test_object = self.series_2
        author = test_object.entry_author

        author.deleted_time = (
            datetime.datetime.now() - datetime.timedelta(days=time_fringe + 100)
        ).replace(tzinfo=datetime.timezone.utc)
        author.deleted = True

        perm = Group.objects.get(name=constants.HANDLE_DELETED_USERS_GROUP)
        user_with_perm = self.series_1.entry_author
        user_with_perm.is_staff = False
        user_with_perm.groups.add(perm)

        self.request.user = user_with_perm

        self.assertTrue(
            permission.has_object_permission(self.request, self.view, test_object)
        )

        user_with_perm.groups.clear()
        user_with_perm.is_staff = True

        self.assertTrue(
            permission.has_object_permission(self.request, self.view, test_object)
        )

