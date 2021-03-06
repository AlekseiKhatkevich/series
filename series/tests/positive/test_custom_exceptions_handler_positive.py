from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class CustomExceptionHandlerPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Test for custom exception handler functions.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user_1, cls.user_2, cls.user_3 = create_test_users.create_users()
        cls.image = initial_data.generate_test_image()

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
        expected_error_code = 'No TvSeriesModel matches the given query.'

        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            reverse('upload', args=(999, 'test.jpg')),
            data={'file': self.image},
            format='jpg',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_404_NOT_FOUND,
            error_message=expected_error_code,
        )

