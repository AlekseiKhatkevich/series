from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.reverse import reverse

from django.contrib.auth import get_user_model

import users.serializers
from users.helpers import create_test_users


class DjoserSerializersPositiveTest(APITestCase):
    """
    Test of custom Djoser's auth serializers and endpoints in general.
    """
    @classmethod
    def setUpTestData(cls):
        cls.user_1, cls.user_2, cls.user_3 = create_test_users.create_users()

    def setUp(self) -> None:
        self.test_user_data = dict(email='test@mail.ru',
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

    def test_add_account_as_slave(self):
        """
        Check whether or not it is possible to add currently created account as a slave account to master
        account.
        """
        self.user_1.set_password('secret_password')
        self.user_1.save()

        master_fields_data = dict(
            master_email=self.user_1.email,
            master_password='secret_password'
        )
        test_user_data = {**self.test_user_data, **master_fields_data}

        response = self.client.post(
            reverse('user-list'),
            data=test_user_data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )
        self.assertEqual(
            self.user_1.pk,
            response.data['master_id']
        )
        self.assertTrue(
            get_user_model().objects.filter(
                master=self.user_1,
                email=test_user_data['email']
            ).exists()
        )
