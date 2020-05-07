from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from django.contrib.auth import get_user_model

import users.serializers


class DjoserSerializersPositiveTest(APITestCase):
    """
    Test of custom Djoser's auth serializers.
    """

    test_user_data = dict(email='test@mail.ru',
                          first_name='Jacky',
                          last_name='Chan',
                          user_country='CN',
                          password='test_password', )

    def test_CustomDjoserUserCreateSerializer(self):
        """
        Check whether or not 'CustomDjoserUserCreateSerializer' now has an ability to work with
        'user_country' field.
        """
        serializer = users.serializers.CustomDjoserUserCreateSerializer(data=self.test_user_data)

        self.assertTrue(
            serializer.is_valid()
        )
        self.assertEqual(
            serializer.data['user_country'],
            self.test_user_data['user_country']
        )

    def test_custom_user_create_endpoint(self):
        """
        Check whether or not it is possible to specify 'user_country' field during user
        creation process via API and save it to DB.
        """

        response = self.client.post(
            reverse('user-list'),
            data=self.test_user_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertTrue(get_user_model().objects.filter(
            email='test@mail.ru', user_country='CN',
        ).exists()
        )
