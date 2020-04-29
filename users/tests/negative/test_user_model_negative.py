from rest_framework.test import APITestCase

from django.db import transaction
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

import unittest

from ...helpers import create_test_users, countries


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

    def test_wrong_user_country_db_constraint(self):
        """
        Check whether or not DB constraint doesnt allow to save wrong country code in DB.
        """
        self.test_user_data['user_country'] = 'XX'
        expected_constraint_name = 'country_code_within_list_of_countries_check'

        #  https://stackoverflow.com/questions/21458387/transactionmanagementerror-you-cant-execute-queries-until-the-end-of-the-atom/61498699#61498699
        with transaction.atomic():
            with self.assertRaisesRegex(IntegrityError, expected_constraint_name):
                get_user_model().objects.create_user(**self.test_user_data)

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

    def test_first_name_and_last_name_unique_together(self):
        """
        Check whether or not is possible to create 2 users with same name and username.
        """
        expected_constraint_name = 'users_user_first_name_last_name'

        get_user_model().objects.create_user(**self.test_user_data)

        with transaction.atomic():
            with self.assertRaisesRegex(IntegrityError, expected_constraint_name):
                self.test_user_data['email'] = 'test_2@mail.ru'
                get_user_model().objects.create_user(**self.test_user_data)

        self.assertFalse(
            get_user_model().objects.filter(email='test_2@mail.ru').exists()
        )

    def slave_doesnt_have


