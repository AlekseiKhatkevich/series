from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import IntegrityError
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
import operator

from users.helpers import countries, create_test_users


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
        cls.user = get_user_model().objects.create_user(**cls.test_user_data)

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()
        super(CreateUserModelPositiveTest, cls).tearDownClass()

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

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

    def test_is_slave_property(self):
        """
        Check whether or not 'is_slave' model property returns True when user is slave
         and other way around.
        """
        self.user_2.master = self.user_1

        self.assertTrue(
            self.user_2.is_slave
        )
        self.assertFalse(
            self.user_1.is_slave
        )

    def test_get_absolute_url(self):
        """
        Check 'get_absolute_url' property correct work.
        """

        self.assertEqual(
            self.user.get_absolute_url,
            reverse(f'{self.user._meta.model_name}-detail', args=(self.user.pk, ))
        )

    def test_is_available_slave(self):
        """
        Check 'is_available_slave' property correct work.
        """
        self.user_1.master = self.user_3
        self.user_1.save()

        self.assertTrue(
            self.user_2.is_available_slave
        )

        for user in (self.user_1, self.user_3):
            with self.subTest(user=user):
                self.assertFalse(
                    user.is_available_slave
                )

    def test_save_full_clean(self):
        """
        Check that if 'FC' argument is in the 'save' method, then model's  'full_clean' method would
        be conjured up.
        """
        #  Validation takes place on model level.
        with self.assertRaises(exceptions.ValidationError):
            self.user_1.master = self.user_1
            self.user_1.save(fc=True)
        #  Validation takes place on DB level.
        with self.assertRaises(IntegrityError):
            self.user_1.master = self.user_1
            self.user_1.save(fc=False)

    def test_delete(self):
        """
        Check that if 'soft_del=True' is present in method arguments, then model instance would be
        soft deleted. If False - hard deleted. If master is soft-deleted -his slaves must be liberated.
        """
        self.user_2.master = self.user_1
        self.user_2.save()
        self.user_1.delete(soft_del=True)
        self.user_2.refresh_from_db()

        self.assertTrue(
            self.user_1.deleted
        )
        self.assertIsNone(
            self.user_2.master
        )

        self.user_3.delete(soft_del=False)

        self.assertFalse(
            get_user_model()._default_manager.filter(pk=self.user_3.pk).exists()
        )

    def test_undelete(self):
        """
        Check that 'undelete' method restore user's soft-deleted entry state to deleted=False.
        """
        self.user_1.delete()
        self.user_1.undelete()
        self.user_1.refresh_from_db()

        self.assertFalse(
            self.user_1.deleted
        )

    def test_liberate(self):
        """
        Check that all users slaves are deallocate.
        """
        self.user_3.master = self.user_2.master = self.user_1
        map(operator.methodcaller('save'), self.users)
        self.user_1.liberate()

        for user in (self.user_3, self.user_2):
            with self.subTest(user=user):
                user.refresh_from_db()
                self.assertIsNone(
                    user.master
                )

    def test_managers(self):
        """
        Check that 'objects.all()' returns all instances without soft-deleted ones , and
        'all_objects.all() -all instances in DB table.
        """
        self.user_1.delete(soft_del=True)

        self.assertFalse(
            get_user_model().objects.filter(pk=self.user_1.pk).exists()
        )
        self.assertTrue(
            get_user_model().all_objects.filter(pk=self.user_1.pk).exists()
        )

