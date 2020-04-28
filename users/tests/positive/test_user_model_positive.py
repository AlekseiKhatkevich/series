from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

from ...helpers import create_test_users, countries


class CreateUserModelPositiveTest(APITestCase):
    """
    Positive test to test smooth user creation process as a model instance.
    """
    test_user_data = dict(email='test@mail.ru',
                          first_name='Jacky',
                          last_name='Chan',
                          user_country='CN',
                          password='test_password', )

    @classmethod
    def setUpTestData(cls):
        create_test_users.create_users()
        cls.user = get_user_model().objects.create_user(**cls.test_user_data)

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()

    def test_create_user(self):
        self.assertTrue(get_user_model().objects.filter(email=self.test_user_data['email']).exists())
        self.assertTrue(self.user.is_active)
        self.assertDictEqual({self.user.user_country: self.user.get_user_country_display()},
                             {(cnt := self.test_user_data['user_country']): countries.COUNTRIES_DICT[cnt]})
        self.assertTrue(self.user.check_password(self.test_user_data['password']))

    def test_str_method(self):
        for param in ('MASTER ACC.', self.user.pk, self.user.get_full_name(), self.user.email):
            self.assertIn(str(param), self.user.__str__())
            from django.conf import settings
        self.assertTrue(settings.IM_IN_TEST_MODE)


