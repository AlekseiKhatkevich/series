import unittest

from django.contrib.auth import get_user_model
from django.core import exceptions
from django.db import models, transaction
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

from series import error_codes
from users.helpers import create_test_users


class CreateUserModelNegativeTest(APITestCase):
    """
    Negative test to test how good code in user models fight against attempts to create user instance
     with bad data.
    """

    def setUp(self) -> None:
        self.test_user_data = dict(email='test@mail.ru',
                                   first_name='Jacky',
                                   last_name='Chan',
                                   user_country='CN',
                                   password='test_password', )

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()
        super(CreateUserModelNegativeTest, cls).tearDownClass()

    def test_wrong_user_country_db_constraint(self):
        """
        Check whether or not DB constraint doesnt allow to save wrong country code in DB.
        Test skipped if 'full_clean' or 'clean' method is used in save().
        """
        self.test_user_data['user_country'] = 'XX'
        expected_constraint_name = 'country_code_within_list_of_countries_check'

        #  https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom/61498699#61498699
        with transaction.atomic(), self.assertRaisesRegex(IntegrityError, expected_constraint_name):
            user = get_user_model().objects.create_user(db_save=False, **self.test_user_data)
            user.save(fc=False)

        self.assertFalse(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )

    def test_master_points_on_itself(self):
        """
        Check DB constraint that prevents model entry from having pk = master_id (point to itself).
        """
        expected_constraint_code = 'point_on_itself_check'

        with transaction.atomic():
            with self.assertRaisesMessage(IntegrityError, expected_constraint_code):
                get_user_model().objects.filter(pk=self.user_1.pk).update(master=models.F('pk'))

        self.user_1.refresh_from_db()

        self.assertNotEqual(
            self.user_1.master,
            self.user_1.pk
        )

    def test_wrong_user_country_validation(self):
        """
        Check whether or not field validator  doesnt allow to save wrong country code in DB.
        """
        self.test_user_data['user_country'] = 'XX'

        with transaction.atomic():
            with self.assertRaises(exceptions.ValidationError):
                user = get_user_model().objects.create_user(db_save=False, **self.test_user_data)
                user.full_clean()
                user.save()

        self.assertFalse(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )

    @unittest.skip(reason='Unique together was removed.')
    def test_first_name_and_last_name_unique_together(self):
        """
        Check whether or not is possible to create 2 users with same name and username.
        """
        expected_constraint_name = 'users_user_first_name_last_name'

        get_user_model().objects.create_user(**self.test_user_data)

        with transaction.atomic():
            with self.assertRaisesRegex(IntegrityError, expected_constraint_name):
                self.test_user_data['email'] = 'test_2@mail.ru'
                user = get_user_model().objects.create_user(db_save=False, **self.test_user_data)
                user.save(fc=False)

        self.assertFalse(
            get_user_model().objects.filter(email='test_2@mail.ru').exists()
        )

    def test_slave_cant_have_slaves_validation(self):
        """
        Test whether or not slave cant have it's own slaves and how clean() method
        in model resists to attempt to validate and save data for this situation.
        """
        master = get_user_model().objects.get(email='superuser@inbox.ru')
        slave = get_user_model().objects.get(email='user_1@inbox.ru')
        slaves_slave = get_user_model().objects.get(email='user_2@inbox.ru')
        expected_error_message = error_codes.SLAVE_CANT_HAVE_SALVES.message

        with transaction.atomic():
            slave.master = master
            slaves_slave.master = slave
            slaves_slave.save()
            with self.assertRaisesRegex(exceptions.ValidationError, expected_error_message):
                slave.clean()
                slave.save()

        slave.refresh_from_db()
        self.assertIsNone(slave.master)

    def test_slave_cant_have_a_master_who_is_a_slave_himself(self):
        """
        Testing that slave cant have a master who is a slave himself.
        """
        master = get_user_model().objects.get(email='superuser@inbox.ru')
        slave = get_user_model().objects.get(email='user_1@inbox.ru')
        slaves_slave = get_user_model().objects.get(email='user_2@inbox.ru')
        expected_error_message = error_codes.MASTER_CANT_BE_SLAVE.message

        with transaction.atomic():
            slave.master = master
            master.master = slaves_slave
            master.save()
            with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
                slave.clean()
                slave.save()

        slave.refresh_from_db()
        self.assertIsNone(slave.master)

    def test_master_can_not_point_itself(self):
        """
        Check part of clean() method validation logic that in charge of defending data from
        being corrupted by specifying master field equal self.
        """
        self.user_1.master = self.user_1
        expected_error_message = error_codes.MASTER_OF_SELF.message

        with transaction.atomic():
            with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
                self.user_1.save()

        self.user_1.refresh_from_db()

        self.assertIsNone(
            self.user_1.master
        )

    def test_have_slaves_or_master_alive(self):
        """
        Check that property 'have_slaves_or_master_alive' returns False if user does not have
         not-soft-deleted slaves or master.
        """
        self.assertFalse(
            self.user_1.have_slaves_or_master_alive
        )
        self.assertFalse(
            self.user_1.have_slaves_or_master_alive
        )

    def test_have_slaves_or_master_alive_slave_soft_deleted(self):
        """
        Check that property 'have_slaves_or_master_alive' returns False if user do have slaves but
        it soft-deleted.
        """
        master = self.user_1
        slave = self.user_2
        master.slaves.add(slave)
        slave.delete(soft_del=True)

        self.assertFalse(
            master.have_slaves_or_master_alive
        )

    def test_have_slaves_or_master_alive_master_soft_deleted(self):
        """
        Check that property 'have_slaves_or_master_alive' returns False if user do have master but
        it soft-deleted.
        """
        master = self.user_1
        slave = self.user_2
        master.slaves.add(slave)
        master.delete(soft_del=True)

        self.assertFalse(
            slave.have_slaves_or_master_alive
        )

    def test_slaves_of_deleted_user_check_constraint(self):
        """
        Check that 'slaves_of_deleted_user_check' would not allow to have slaves to user
         with 'deleted' = True.
        """
        expected_error_message = 'slaves_of_deleted_user_check'
        master = self.user_1
        slave = self.user_2
        master.slaves.add(slave)
        master.deleted = True

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            master.save(fc=False)

    def test_slaves_of_deleted_user_clean(self):
        """
        Check that 'slaves_of_deleted_user_check' would not allow to have slaves to user
         with 'deleted' = True by clean(0 method in model.
        """
        expected_error_message = error_codes.DELETED_MASTER_SLAVES.message
        master = self.user_1
        slave = self.user_2
        master.slaves.add(slave)
        master.deleted = True

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            master.save(fc=True)









