from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model


class CreateSuperUserPositiveTest(APITestCase):
    """
    Test to check superuser smooth creation.
    """
    test_user_data = dict(email='test@mail.ru',
                          first_name='Jacky',
                          last_name='Chan',
                          user_country='CN',
                          password='test_password', )

    def test_create_superuser(self):
        """
        Check whether or not providing correct user data superuser can be created and saved in DB
        correctly with proper field set wit proper data and flags.
        """
        user = get_user_model().objects.create_superuser(
            **self.test_user_data
        )
        self.assertTrue(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )
        for attr in (user.is_superuser, user.is_staff, user.is_active):
            with self.subTest(attr=attr):
                self.assertTrue(attr)



