import re

from django.conf import settings
from django.contrib.auth import get_user_model, tokens
from django.core import mail
from django.core.cache import caches
from djoser import utils
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from rest_framework_simplejwt.authentication import JWTAuthentication

import users.serializers
from series.helpers import custom_functions
from users.helpers import context_managers, create_test_ips, create_test_users


class DjoserCreateUerPositiveTest(APITestCase):
    """
    Test of custom Djoser's auth create user endpoint.
    auth/users/ POST
    """

    def setUp(self) -> None:
        self.test_user_data = dict(
            email='test@mail.ru',
            first_name='Jacky',
            last_name='Chan',
            user_country='CN',
            password='test_password',
        )
        self.user_1, self.user_2, self.user_3 = create_test_users.create_users()

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


class DjoserUsersListPositiveTest(APITestCase):
    """
    Test for Djoser endpoint that shows list of users for admin and self just for regular user.
    auth/users/ GET
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_extra_fields(self):
        """
        Check that 3 extra added fields - 'user_country', 'master', 'slave_accounts_ids'
        are rendered properly.
        """
        self.user_2.master = self.user_3.master = self.user_1

        self.user_2.save()
        self.user_3.save()

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('user-list'),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        #  check that user_1 have user2 and user_3 specified as slaves in field 'slave_accounts_ids'.
        self.assertCountEqual(
            [self.user_2.pk, self.user_3.pk],
            [slave_accounts_ids for user in response.data['results'] if
             (slave_accounts_ids := user['slave_accounts_ids']) is not None][0],
        )

        users_to_countries_in_response = \
            custom_functions.key_field_to_field_dict(response, 'email', 'user_country')
        users_to_countries_original = {user.email: user.user_country for user in self.users}
        # Check that countries are shown correctly
        self.assertDictEqual(
            users_to_countries_in_response,
            users_to_countries_original
        )

        users_to_master_in_response = custom_functions.key_field_to_field_dict(response, 'email', 'master')
        users_to_master_original = {user.email: user.master_id for user in self.users}
        # Check that master is correctly shown in response data.
        self.assertDictEqual(
            users_to_master_in_response,
            users_to_master_original
        )


class SetSlavesPositiveTest(APITestCase):
    """
    Test on Djoser custom endpoint that attaches slave to master.
    /auth/users/set_slaves/ POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.password = 'my_secret_password'
        cls.user_3.set_password(cls.password)
        cls.user_3.save()

    def tearDown(self) -> None:
        mail.outbox = []

    def test_set_slave_SEND_ACTIVATION_EMAIL_False(self):
        """
        Check whether endpoint provided with correct data is able to correctly attach slave account
        to user account.
        'SEND_ACTIVATION_EMAIL' = False, that is we dont send activation email but rather attach slave
        directly.
        """
        data = dict(
            slave_email=self.user_3.email,
            slave_password=self.password,
        )

        self.client.force_authenticate(user=self.user_1)

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=False):
            response = self.client.post(
                reverse('user-set-slaves'),
                data=data,
                format='json',
            )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED
        )

        self.user_3.refresh_from_db()

        self.assertEqual(
            self.user_3.master,
            self.user_1
        )

    def test_set_slave_SEND_ACTIVATION_EMAIL_True(self):
        """
        Check that if 'SEND_ACTIVATION_EMAIL' option in settings is set to True, slave will not be attached to
        master immediately after api call, but rather confirmation letter would be sent to slave.
        """
        potential_slave = self.user_3
        potential_master = self.user_1

        data = dict(
            slave_email=potential_slave.email,
            slave_password=self.password,
        )
        self.client.force_authenticate(user=potential_master)

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-set-slaves'),
                data=data,
                format='json',
            )
        potential_slave.refresh_from_db()
        #  url from email sent.
        url = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group('url')
        master_uid, slave_uid, token = url.split('/')[-3:]

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED
        )
        # Check that slave was not attached to master.
        self.assertIsNone(
            potential_slave.master
        )
        # Check that email has been sent.
        self.assertEqual(
            len(mail.outbox),
            1,
        )
        # Check subject in order to make sure that correct email is sent.
        self.assertEqual(
            mail.outbox[0].subject,
            f'Slave account attachment confirmation on {settings.SITE_NAME}',
        )
        #  Check that email recipient is the potential slave.
        self.assertEqual(
            mail.outbox[0].to[0],
            potential_slave.email,
        )

        # Make sure that master UID extracted from email url is coincide to master ID after decoding.
        self.assertEqual(
            int(utils.decode_uid(master_uid)),
            potential_master.pk
        )
        # Make sure that slave UID extracted from email url is coincide to slave ID after decoding.
        self.assertEqual(
            int(utils.decode_uid(slave_uid)),
            potential_slave.pk
        )
        # Make sure that slave token extracted from email is valid.
        self.assertTrue(
            tokens.default_token_generator.check_token(user=potential_slave, token=token)
        )


class UserUndeletePositiveTest(APITestCase):
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
        mail.outbox = []
        caches['throttling'].clear()

    def test_undelete_without_confirmation_email(self):
        """
        Check that if 'SEND_ACTIVATION_EMAIL' flag in settings is set to False, than soft-deleted
        user with correct email and password can undelete his account instantly.
        """
        self.user_3.delete()
        data = dict(
            email=self.user_3.email,
            password=self.password,
        )
        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=False):
            response = self.client.post(
                reverse('user-undelete-account'),
                data=data,
                format='json',
            )
        self.user_3.refresh_from_db()

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertFalse(
            self.user_3.deleted
        )

    def test_undelete_with_confirmation_email(self):
        """
        Check that if 'SEND_ACTIVATION_EMAIL' flag in settings is set to True, than soft-deleted
        user with correct email and password should receive email with confirmation link and meanwhile
        his account should remain soft-deleted.
        """
        self.user_3.delete()
        data = dict(
            email=self.user_3.email,
            password=self.password,
        )
        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-undelete-account'),
                data=data,
                format='json',
            )
        self.user_3.refresh_from_db()
        url = re.search("(?P<url>https?://[^\s]+)", mail.outbox[0].body).group('url')
        uid, token = url.split('/')[-2:]

        self.assertEqual(
            response.status_code,
            status.HTTP_202_ACCEPTED
        )
        self.assertTrue(
            self.user_3.deleted
        )
        self.assertEqual(
            len(mail.outbox),
            1,
        )
        self.assertEqual(
            mail.outbox[0].subject,
            f'Account undelete confirmation on {settings.SITE_NAME}',
        )
        self.assertEqual(
            mail.outbox[0].to[0],
            self.user_3.email,
        )
        self.assertEqual(
            int(utils.decode_uid(uid)),
            self.user_3.pk,
        )
        self.assertTrue(
            tokens.default_token_generator.check_token(user=self.user_3, token=token)
        )


class RefreshTokenEndpointPositiveTest(APITestCase):
    """
    Test that when user demands new access token, his ip is determined and written in DB.
    Also check that whole endpoint works correctly after customization.
    auth/jwt/refresh/ POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_writing_ip_in_DB(self):
        """
        Check that user's ip is saved in DB.
        """
        refresh_token = self.user_2.get_tokens_for_user()['refresh']
        data = {'refresh': refresh_token}
        fake_ip = '228.228.228.228'

        response = self.client.post(
            reverse('jwt-refresh'),
            data=data,
            format='json',
            HTTP_X_FORWARDED_FOR=fake_ip,
            REMOTE_ADDR=fake_ip,
        )
        jwt_auth = JWTAuthentication()
        access_token = jwt_auth.get_validated_token(response.data["access"])
        user_from_token = jwt_auth.get_user(access_token)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )
        self.assertEqual(
            self.user_2.user_ip.first().ip,
            fake_ip
        )
        self.assertEqual(
            self.user_2,
            user_from_token
        )


class UserResendActivationEmailPositiveTest(APITestCase):
    """
    Positive test for User resent activation email API custom permission class.
    auth/users/resend_activation/ POST
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def setUp(self) -> None:
        create_test_ips.create_ip_entries(self.users)

    def test_UserIPPermission_ip_in_db(self):
        """
        Check that if request comes from a machine which ip address we have in DB associated with the user,
        whose email is provided, then requests passes trough.
        """
        self.user_2.is_active = False
        self.user_2.save()
        ip = self.user_2.user_ip.all().order_by('?').first().ip
        data = {'email': self.user_2.email}

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
            status.HTTP_204_NO_CONTENT
        )

    def test_UserIPPermission_user_has_no_ip_entry(self):
        """
        Check if user with email from request.data doesnt have any associated saved ip addresses in DB,
        then he would be able to get access to API.
        """
        self.user_3.is_active = False
        self.user_3.save()
        self.user_3.user_ip.all().delete()
        data = {'email': self.user_3.email}

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-resend-activation'),
                data=data,
                format='json',
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )

    def test_UserIPPermission_user_is_admin(self):
        """
        Check if user is admin, then it has access to ip entirely.
        """
        self.user_3.is_active = False
        self.user_3.save()
        data = {'email': self.user_3.email}

        self.client.force_authenticate(user=self.user_1)

        with context_managers.OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=True):
            response = self.client.post(
                reverse('user-resend-activation'),
                data=data,
                format='json',
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
