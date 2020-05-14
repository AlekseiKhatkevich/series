from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from users.helpers import create_test_users


class UserManagerAndQuerysetPositiveTest(APITestCase):
    """
    Test for User model manager and queryset methods.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_get_available_slaves(self):
        """
         Check that method 'get_available_slaves'of User model queryset returns queryset with
         only available slaves.
        """
        self.user_3.master = self.user_1
        self.user_3.save()

        #  only user_2 is available slave.
        with self.assertNumQueries(2):
            self.assertQuerysetEqual(
                get_user_model().objects.get_available_slaves(),
                get_user_model().objects.filter(email=self.user_2.email),
                ordered=False,
                transform=lambda x: x
            )

    def test_check_user_and_password_method(self):
        """
        Check whether or not method 'check_user_and_password' returns user instance provided that correct
        input data has been received.
        """
        self.user_1.set_password('secret')
        self.user_1.save()

        user = get_user_model().objects.check_user_and_password(
            email=self.user_1.email,
            password='secret'
        )

        self.assertEqual(
            self.user_1,
            user
        )

