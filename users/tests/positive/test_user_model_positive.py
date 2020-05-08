from rest_framework.test import APITestCase
from rest_framework.reverse import reverse

from django.contrib.auth import get_user_model

from users.helpers import create_test_users, countries


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
        super(CreateUserModelPositiveTest, cls).tearDownClass()

    def test_create_user(self):
        """
        Check whether or not instance of user is created after correct data has passed to constructor.
        """
        self.assertTrue(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )
        self.assertTrue(
            self.user.is_active
        )
        self.assertDictEqual(
            {self.user.user_country: self.user.get_user_country_display()},
            {(cnt := self.test_user_data['user_country']): countries.COUNTRIES_DICT[cnt]}
        )
        self.assertTrue(
            self.user.check_password(self.test_user_data['password'])
        )

    def test_str_method(self):
        """
        Check whether or not __STR__ method works as intended.
        """
        for param in ('MASTER ACC.', self.user.pk, self.user.get_full_name(), self.user.email):
            with self.subTest(param=param):
                self.assertIn(str(param), self.user.__str__())

    def test_my_slaves(self):
        """
        Check whether or not class property 'my_slaves' returns list of user's slaves (slave accounts).
        """
        potential_slaves = get_user_model().objects.exclude(email=self.user.email)
        potential_slaves.update(master=self.user)

        self.assertCountEqual(
            self.user.my_slaves, potential_slaves
        )

    def test_get_absolute_url(self):
        """
        Check 'get_absolute_url' method correct work.
        """

        self.assertEqual(
            self.user.get_absolute_url,
            reverse(f'{self.user._meta.model_name}-detail', args=(self.user.pk, ))
        )
