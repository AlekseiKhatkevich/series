from rest_framework import generics
from rest_framework.test import APIRequestFactory, APITestCase

import series.permissions
from users.helpers import create_test_users


class PermissionPositiveTest(APITestCase):
    """
    Positive test on series project root custom permissions.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.view = generics.GenericAPIView()

    def setUp(self) -> None:
        self.request = APIRequestFactory().request()

    def test_SoftDeletedUsersDenied(self):
        """
        Check that 'SoftDeletedUsersDenied' returns True is user is not soft-deleted.
        """
        permission = series.permissions.SoftDeletedUsersDenied()
        test_user = self.user_1
        self.request.user = test_user

        self.assertFalse(
            test_user.deleted
        )
        self.assertTrue(
            permission.has_permission(self.request, self.view)
        )

