import datetime

from django.contrib.auth.models import AnonymousUser, Group
from rest_framework import generics
from rest_framework.test import APIRequestFactory, APITestCase
import more_itertools
import archives.permissions
from archives.tests.data import initial_data
from series import constants
from users.helpers import create_test_users


class PermissionNegativeTest(APITestCase):
    """
    Negative test on 'archives' app custom permissions.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users
        cls.anonymous = AnonymousUser()

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.view = generics.GenericAPIView()
        self.request = APIRequestFactory().request()

    def test_ReadOnlyIfOnlyAuthenticated(self):
        """
        Check that 'ReadOnlyIfOnlyAuthenticated' permission returns False if user is not
        authenticated or request method is not in safe methods.
        """
        permission = archives.permissions.ReadOnlyIfOnlyAuthenticated()
        self.request.user = self.anonymous

        self.assertFalse(
            permission.has_permission(self.request, self.view)
        )
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, self.series_1)
        )

        self.request.method = 'POST'
        self.request.user = self.user_1

        self.assertFalse(
            permission.has_permission(self.request, self.view)
        )
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, self.series_1)
        )

    def test_IsObjectOwner(self):
        """
        Check that 'IsObjectOwner' returns False if object author is not a request user.
        """
        permission = archives.permissions.IsObjectOwner()
        obj = self.series_1
        not_an_author = self.series_2.entry_author
        self.request.user = not_an_author

        self.assertFalse(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_MasterSlaveRelations(self):
        """
        Check that 'MasterSlaveRelations' permission returns False if request user is not a slave or master of
        object author.
        """
        permission = archives.permissions.MasterSlaveRelations()
        obj = self.series_1
        random_person = self.series_2.entry_author

        self.request.user = random_person

        self.assertFalse(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_FriendsGuardianPermission(self):
        """
        Check that 'FriendsGuardianPermission' permission returns False if request user do not have permission
        'DEFAULT_OBJECT_LEVEL_PERMISSION_CODE' on this object or on object's series.
        """
        permission = archives.permissions.FriendsGuardianPermission()
        obj = self.series_1
        random_person = self.series_2.entry_author
        self.request.user = random_person

        self.assertFalse(
            permission.has_object_permission(self.request, self.view, obj)
        )

    def test_HandleDeletedUsersEntriesPermission(self):
        """
        Check that 'HandleDeletedUsersEntriesPermission' permission returns False in:
        a) deleted_time is Null.
        b) object author is not soft-deleted.
        c) if object author is soft-deleted but less then half-year had elapsed since this took
        place.
        d) request user is not staff or dont not have special permission.
        """
        permission = archives.permissions.HandleDeletedUsersEntriesPermission()
        time_fringe = constants.DAYS_ELAPSED_SOFT_DELETED_USER

        test_object = self.series_2

        perm = Group.objects.get(name=constants.HANDLE_DELETED_USERS_GROUP)
        user_with_perm = self.series_1.entry_author
        user_with_perm.is_staff = False
        user_with_perm.groups.add(perm)

        self.request.user = user_with_perm
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        author = test_object.entry_author
        author.deleted_time = None
        author.deleted = True

        #  If deleted_time is None -> False
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, test_object)
        )
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        author.deleted_time = (
            datetime.datetime.now() - datetime.timedelta(days=time_fringe + 100)
        ).replace(tzinfo=datetime.timezone.utc)
        author.deleted = False

        #  If deleted = False-> False
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, test_object)
        )
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        author.deleted_time = (
                datetime.datetime.now() - datetime.timedelta(days=time_fringe - 1)
        ).replace(tzinfo=datetime.timezone.utc)
        author.deleted = True

        # If timedelta les than half-year.
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, test_object)
        )
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        author.deleted_time = (
                datetime.datetime.now() - datetime.timedelta(days=time_fringe + 100)
        ).replace(tzinfo=datetime.timezone.utc)
        author.deleted = True

        user_with_perm.is_staff = False
        user_with_perm.groups.clear()

        # If user is not staff and dont have special permission.
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, test_object)
        )
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        user_with_perm.is_staff = True

        slave = more_itertools.first_true(
            self.users,
            lambda user: user != author and user != user_with_perm,
        )
        author.slaves.add(slave)

        # If author has slaves or master alive -> False
        self.assertFalse(
            permission.has_object_permission(self.request, self.view, test_object)
        )
        slave.master = None
