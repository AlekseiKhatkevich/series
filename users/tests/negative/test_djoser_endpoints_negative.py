from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

import users.serializers
from users.helpers import create_test_users

from series import error_codes


class DjoserSerializersNegativeTest(APITestCase):
    """
    Test of custom Djoser's auth serializers.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user_1, cls.user_2, cls.user_3 = create_test_users.create_users()
        cls.user_1.set_password('secret_password')
        cls.user_1.save(update_fields=('password', ))

    def setUp(self) -> None:
        self.test_user_data = dict(
            email='test@mail.ru',
            first_name='Jacky',
            last_name='Chan',
            user_country='CN',
            password='test_password',
        )
        self.master_fields = dict(
            master_email=self.user_1.email,
            master_password='secret_password'
        )

    def test_CustomDjoserUserCreateSerializer(self):
        """
        Check whether or not 'CustomDjoserUserCreateSerializer' can not validate wrong country code.
        """
        self.test_user_data['user_country'] = 'XX'
        serializer = users.serializers.CustomDjoserUserCreateSerializer(data=self.test_user_data)
        expected_error_message = {
            "user_country": [
                error_codes.WRONG_COUNTRY_CODE.message
            ]
        }

        self.assertFalse(
            serializer.is_valid()
        )
        self.assertEqual(
            serializer.data['user_country'],
            self.test_user_data['user_country']
        )
        self.assertEqual(
            serializer.errors,
            expected_error_message
        )

    def test_wrong_country_code_custom_message(self):
        """
        Check whether or not response returns custom message in case country code is invalid.
        """
        self.test_user_data['user_country'] = 'XX'
        expected_error_message = {
            "user_country": [
                error_codes.WRONG_COUNTRY_CODE.message
            ]}
        response = self.client.post(
            reverse('user-list'),
            data=self.test_user_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data,
            expected_error_message
        )

    def test_not_all_master_fields(self):
        """
        Check that exception is arisen if not all master fields ('master_password', 'master_email', )
        are present in incoming data.
        """
        del self.master_fields['master_password']

        response = self.client.post(
            reverse('user-list'),
            data={**self.test_user_data, **self.master_fields},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['master_password'][0],
            error_codes.MASTER_FIELDS_REQUIRED.message
        )

    def test_validate_master_fields_wrong_master_email(self):
        """
        Check whether exception is arisen if master email is not belong to any user in DB.
        """
        self.master_fields['master_email'] = 'fake_user@gmail.com'

        response = self.client.post(
            reverse('user-list'),
            data={**self.test_user_data, **self.master_fields},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['user_email'][0],
            error_codes.USER_DOESNT_EXISTS.message
        )

    def test_validate_master_fields_wrong_master_password(self):
        """
        Check whether exception is arisen if master password is wrong.
        """
        self.master_fields['master_password'] = 'wrong_password'
        master_email = self.master_fields['master_email']
        expected_error_message = f'Incorrect password for user with email - {master_email}'

        response = self.client.post(
            reverse('user-list'),
            data={**self.test_user_data, **self.master_fields},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['user_password'][0],
            expected_error_message
        )
