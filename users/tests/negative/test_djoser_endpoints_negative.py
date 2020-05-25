from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from rest_framework import status, throttling
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import users.serializers
from series import error_codes
from series.helpers.test_helpers import TestHelpers
from users.helpers import context_managers, create_test_ips, create_test_users


class DjoserUserCreateNegativeTest(APITestCase):
    """
    Test of custom Djoser's user create endpoint.
    /auth/users/ POST
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

    def test_attempt_create_user_with_email_equal_soft_deleted_user(self):
        """
        Check that endpoint would not allow to create user account with email that coincide
        with email of soft-deleted user account. And we would receive non-standard custom error
        message in this scenario.
        """
        test_user = get_user_model().objects.create_user(**self.test_user_data)
        test_user.delete()

        response = self.client.post(
            reverse('user-list'),
            data={**self.test_user_data},
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['email'][0],
            error_codes.USER_SOFT_DELETED
        )


class SetSlavesNegativeTest(APITestCase):
    """
    Test on Djoser custom endpoint that attaches slave to master. Test whether or not endpoint's
    serializer resists against attempts of putting inside it bad data.
    /auth/users/set_slaves/ POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.password = 'my_secret_password228882'
        cls.user_3.set_password(cls.password)
        cls.user_3.save()

    def test_slave_is_not_available(self):
        """
        Check that endpoint will resists to attempt to set a slave that is not an available,
        that is already someone's slave or master.
        """
        self.user_3.master = self.user_1
        self.user_3.save()

        data = dict(
            slave_email=self.user_3.email,
            slave_password=self.password,
        )
        expected_error_message = error_codes.SLAVE_UNAVAILABLE.message

        self.client.force_authenticate(user=self.user_1)

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=False):
            response = self.client.post(
                reverse('user-set-slaves'),
                data=data,
                format='json',
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['slave_email'][0],
            expected_error_message
        )

    def test_slave_equal_user(self):
        """
        Check whether validation error is arisen in case user trying to use his own credentials
        as a slave credentials.
        """
        data = dict(
            slave_email=self.user_3.email,
            slave_password=self.password,
        )
        expected_error_message = error_codes.MASTER_OF_SELF.message

        self.client.force_authenticate(user=self.user_3)

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=False):
            response = self.client.post(
                reverse('user-set-slaves'),
                data=data,
                format='json',
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
        self.assertEqual(
            response.data['slave_email'][0],
            expected_error_message
        )


class UserResendActivationEmailNegativeTest(APITestCase):
    """
    Negative test for User resent activation email API custom permission class.
    we check how well permission class secure api from wrong requests.
    auth/users/resend_activation/ POST
    """

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users
        create_test_ips.create_ip_entries(self.users)

    def tearDown(self) -> None:
        caches['throttling'].clear()

    def test_no_email_field(self):
        """
        Check that if no 'email' field in request data, 400 error code with proper error message
        would be returned.
        """
        data = {'efail': 'fail'}
        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-resend-activation'),
                data=data,
                format='json',
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            response.data['detail'],
            error_codes.EMAIL_REQUIRED.message
        )

    def test_ip_not_in_db(self):
        """
        Check that if request came from a machine from ip which we dont have in DB and user
        associated with email provided has ip entries in DB, then request would be rejected.
        """
        self.user_2.is_active = False
        self.user_2.save()
        self.user_2.user_ip.all().update(ip='228.228.228.228')
        data = {'email': self.user_2.email}
        fake_ip = '222.222.222.222'

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-resend-activation'),
                data=data,
                format='json',
                HTTP_X_FORWARDED_FOR=fake_ip,
                REMOTE_ADDR=fake_ip,
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )
        self.assertEqual(
            response.data['detail'],
            error_codes.SUSPICIOUS_REQUEST.message
        )

    def test_throttling(self):
        """
        Check that throttling works correctly.
        """
        self.user_2.is_active = False
        self.user_2.save()
        ip = self.user_2.user_ip.all().order_by('?').first().ip
        data = {'email': self.user_2.email}
        rate = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['resend_activation']
        overflow_rate = throttling.ScopedRateThrottle().parse_rate(rate)[0] + 1

        for _ in range(overflow_rate):
            with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
                response = self.client.post(
                    reverse('user-resend-activation'),
                    data=data,
                    format='json',
                    HTTP_X_FORWARDED_FOR=ip,
                    REMOTE_ADDR=ip,
                )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS
        )

        cache_key = throttling.ScopedRateThrottle.cache_format % {
            'scope': 'resend_activation',
            'ident': ip
        }
        caches['throttling'].delete(cache_key)


class UserUndeleteNegativeTest(APITestCase):
    """
    Test for endpoint for user account undelete.
    /auth/users/undelete_account/ POST
    """

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.password = 'my_secret_password'
        self.user_3.set_password(self.password)
        self.user_3.save()

    def tearDown(self) -> None:
        caches['throttling'].clear()

    def test_user_is_not_deleted(self):
        """
        Check that if user is not-soft deleted, exception would be arisen.
        """
        data = dict(
            email=self.user_3.email,
            password=self.password
        )
        expected_error_message = error_codes.NOT_SOFT_DELETED.message

        response = self.client.post(
            reverse('user-undelete-account'),
            data=data,
            format='json',
        )
        TestHelpers().check_status_and_error(
            response,
            field='email',
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_throttling(self):
        """
        Check that throttling is applied.
        """
        self.user_3.delete()
        data = dict(
            email=self.user_3.email,
            password=self.password
        )
        rate = settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']['undelete_account']
        overflow_rate = throttling.ScopedRateThrottle().parse_rate(rate)[0] + 1

        for _ in range(overflow_rate):
            response = self.client.post(
                reverse('user-undelete-account'),
                data=data,
                format='json',
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS
        )


class JWTTokenObtainNegativeTest(APITestCase):
    """
    Test on JWT token obtain endpoint.
    /auth/jwt/create/ POST
    """
    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.password = 'my_secret_password'
        self.user_3.set_password(self.password)
        self.user_3.save()

    def tearDown(self) -> None:
        caches['throttling'].clear()

    def test_soft_deleted_user_tries_to_obtain_new_toke_pair(self):
        """
        Check that soft-deleted user can't obtain new JWT token pair.
        """
        self.user_3.delete()
        data = dict(
            email=self.user_3.email,
            password=self.password
        )
        expected_error_message = error_codes.SOFT_DELETED_DENIED.message

        response = self.client.post(
            reverse('jwt-create'),
            data=data,
            format='json',
        )
        TestHelpers().check_status_and_error(
            response,
            field='email',
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class RefreshTokenEndpointNegativeTest(APITestCase):
    """
    Test on JWT token refresh API endpoint.
    auth/jwt/refresh/ POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_soft_deleted_user_not_gonna_have_access(self):
        """
        Check that soft-deleted user is not allowed to refresh his token.
        """
        refresh_token = self.user_2.get_tokens_for_user()['refresh']
        data = {'refresh': refresh_token}
        expected_error_message = error_codes.SOFT_DELETED_DENIED.message
        self.user_2.delete()

        response = self.client.post(
            reverse('jwt-refresh'),
            data=data,
            format='json',
        )
        TestHelpers().check_status_and_error(
            response,
            field='email',
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST
        )

