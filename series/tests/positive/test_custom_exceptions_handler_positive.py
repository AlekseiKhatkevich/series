from rest_framework.test import APITestCase
from rest_framework.reverse import reverse
from rest_framework import status
from archives.tests.data import initial_data
from users.helpers import create_test_users

from series import error_codes


class CustomExceptionHandlerPositiveTest(APITestCase):
    """
    Test for custom exception handler functions.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user_1, cls.user_2, cls.user_3 = create_test_users.create_users()

    def setUp(self) -> None:
        self.test_user_data = dict(
            email='test@mail.ru',
            first_name='Jacky',
            last_name='Chan',
            user_country='CN',
            password='test_password',
        )

    def test_handle_django_validation_error(self):
        """
        Check whether we have DRF Response with  400 error instead of standard Django style response
        with 500 error.
        We try to apply salve's account as a master account which should arise ValidationError in clean()
        method in User model
        """
        master = self.user_1
        slave = self.user_2
        expected_error_message = error_codes.MASTER_CANT_BE_SLAVE.message

        slave.master = master
        slave.set_password('secret_password')
        slave.save()

        master_fields = dict(
            master_email=slave.email,
            master_password='secret_password'
        )

        response = self.client.post(
            reverse('user-list'),
            data={**self.test_user_data, **master_fields},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['master'][0],
            expected_error_message
        )

    def test_django_404_error(self):
        """
        Check that descriptive error message is provided on Django 404 error.
        """
        f = open(r'Breaking-Bad-with-Walter-White-320x240_bVh7ibq.jpg', 'rb')
        data = {'file': open(r'Breaking-Bad-with-Walter-White-320x240_bVh7ibq.jpg', 'rb')}
        from django.core.files.uploadedfile import SimpleUploadedFile
        uploaded_file = SimpleUploadedFile('test.jpg', f.read(), 'image/jpeg')
        data = {'file': uploaded_file}

        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            reverse('upload', args=(99999999, 'filename.jpg')),
            data=data,
            format='jpg',
        )
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_404_NOT_FOUND
        # )
        self.assertEqual(
            response.data['image'],
            'sfdgdgdfgdfg'
        )

