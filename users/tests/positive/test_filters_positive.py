import operator

import more_itertools
from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from series.helpers import custom_functions
from users.helpers import create_test_users


class UsersFiltersPositiveTest(APITestCase):
    """
    Positive test on 'users' app filters.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.master = cls.user_1
        cls.slave = cls.user_2
        cls.nobody = cls.user_3

        cls.master.slaves.add(cls.slave)

        cls.superuser = more_itertools.first_true(
            cls.users,
            operator.attrgetter('is_superuser')
        )

    def setUp(self) -> None:
        self.query_dict = QueryDict(mutable=True)
        self.query_dict_2 = QueryDict(mutable=True)

    def test_masters(self):
        """
        Check that 'masters' filter would return only masters on True.
        Check that'slaves' filter would return only slaves on True.
        """
        self.query_dict['masters'] = True
        self.query_dict_2['slaves'] = True

        self.client.force_authenticate(user=self.superuser)

        for dictionary, field in zip(
                (self.query_dict, self.query_dict_2),
                ('slave_accounts_ids', 'master',)
        ):
            with self.subTest(dictionary=dictionary, field=field):
                response = self.client.get(
                    reverse('user-list') + '?' + dictionary.urlencode(),
                    data=None,
                    format='json',
                )

                response_dict = custom_functions.response_to_dict(response, key_field='id')

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )
                self.assertTrue(
                    all([user[field] for user in response_dict.values()])
                )

