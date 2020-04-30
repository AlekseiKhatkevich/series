from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from ...helpers import create_test_users


class CreateTestUsersPositiveTest(APITestCase):
    """
    Test creation of test users by script.
    """
    @classmethod
    def setUpTestData(cls):
        create_test_users.create_users()

    def test_create_test_users(self):
        """
        Check whether or not 3 test users were created.
        """
        self.assertEqual(
            get_user_model().objects.count(), 3
        )

    def test_delete_test_users(self):
        """
        Check whether or not 'delete_users()' deletes all 3 test users.
        """
        create_test_users.delete_users()
        self.assertFalse(
            get_user_model().objects.all().exists()
        )