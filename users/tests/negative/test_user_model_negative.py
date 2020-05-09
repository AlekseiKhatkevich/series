from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from rest_framework.test import APITestCase

from users.helpers import create_test_users

from series import error_codes


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
        create_test_users.create_users()

    @classmethod
    def tearDownClass(cls):
        get_user_model().objects.all().delete()
        super(CreateUserModelNegativeTest, cls).tearDownClass()

    # @unittest.skipIf(custom_functions.check_code_inside(
    #     func=get_user_model().save,
    #     code=('full_clean()', 'clean()'), ),
    #     reason='Wrong country will be validated on the model level '
    # )
    def test_wrong_user_country_db_constraint(self):
        """
        Check whether or not DB constraint doesnt allow to save wrong country code in DB.
        Test skipped if 'full_clean' or 'clean' method is used in save().
        """
        self.test_user_data['user_country'] = 'XX'
        expected_constraint_name = 'country_code_within_list_of_countries_check'

        #  https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom/61498699#61498699
        with transaction.atomic():
            with self.assertRaisesRegex(IntegrityError, expected_constraint_name):
                user = get_user_model().objects.create_user(db_save=False, **self.test_user_data)
                user.save(fc=False)

        self.assertFalse(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )

    def test_wrong_user_country_validation(self):
        """
        Check whether or not field validator  doesnt allow to save wrong country code in DB.
        """
        self.test_user_data['user_country'] = 'XX'

        with transaction.atomic():
            with self.assertRaises(ValidationError, ):
                user = get_user_model().objects.create_user(db_save=False, **self.test_user_data)
                user.full_clean()
                user.save()

        self.assertFalse(
            get_user_model().objects.filter(email=self.test_user_data['email']).exists()
        )

    # @unittest.skipIf(custom_functions.check_code_inside(
    #     func=get_user_model().save,
    #     code=('full_clean()', 'clean()'), ),
    #     reason='Uniqueness will be validated on the model level '
    # )
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
        expected_error_message = error_codes.SLAVE_CANT_HAVE_SALVES

        with transaction.atomic():
            slave.master = master
            slaves_slave.master = slave
            slaves_slave.save()
            with self.assertRaisesRegex(ValidationError, expected_error_message) as cm:
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
        expected_error_message = error_codes.MASTER_CANT_BE_SLAVE

        with transaction.atomic():
            slave.master = master
            master.master = slaves_slave
            master.save()
            with self.assertRaisesRegex(ValidationError, expected_error_message):
                slave.clean()
                slave.save()

        slave.refresh_from_db()
        self.assertIsNone(slave.master)


