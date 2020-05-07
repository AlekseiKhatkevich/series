from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from django.contrib.auth import get_user_model

import users.serializers


class DjoserSerializersNegativeTest(APITestCase):
    """
    Test of custom Djoser's auth serializers.
    """

    def setUp(self) -> None:
        self.test_user_data = dict(email='test@mail.ru',
                                   first_name='Jacky',
                                   last_name='Chan',
                                   user_country='CN',
                                   password='test_password', )

    def test_CustomDjoserUserCreateSerializer(self):
        """
        Check whether or not 'CustomDjoserUserCreateSerializer' can not validate wrong country code.
        """
        self.test_user_data['user_country'] = 'XX'
        serializer = users.serializers.CustomDjoserUserCreateSerializer(data=self.test_user_data)
        expected_error_message = {
            "user_country": [
                "Wrong country code. Country code should consist of 2 uppercase letters according ISO 3166"
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
                "Wrong country code. Country code should consist of 2 uppercase letters according ISO 3166"
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
