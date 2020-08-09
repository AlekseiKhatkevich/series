import operator

import more_itertools
from django.http import QueryDict
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.models
from administration.helpers.initial_data import generate_changelog
from archives.tests.data import initial_data
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
        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.images = initial_data.create_images_instances(cls.series, num_img=2)
        cls.image_1_1, cls.image_1_2, cls.image_2_1, cls.image_2_2 = cls.images

        cls.seasons, cls.seasons_dict = initial_data.create_seasons(
            cls.series,
            num_seasons=3,
            return_sorted=True,
        )
        cls.season_1_1, cls.season_1_2, cls.season_1_3, *series_2_seasons = cls.seasons

        cls.image_model_name = archives.models.ImageModel._meta.model_name
        cls.series_model_name = archives.models.TvSeriesModel._meta.model_name
        cls.season_model_name = archives.models.SeasonModel._meta.model_name
        cls.model_names = (cls.image_model_name, cls.season_model_name, cls.series_model_name,)

        cls.logs_series = generate_changelog(cls.series_1, cls.user_1, num_logs=6)
        cls.logs_seasons = generate_changelog(cls.season_1_1, cls.user_1, num_logs=6)
        cls.logs_images = generate_changelog(cls.image_1_1, cls.user_1, num_logs=6)

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
                (self.query_dict, self.query_dict_2,),
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

    def test_last_operations(self):
        """
        Check that option 'last_operations' in filterset 'UserOperationsHistoryFilter' actually
        returns last entries in each model.
        """
        self.query_dict['model'] = self.series_model_name
        self.query_dict.update({'model': self.season_model_name})
        self.query_dict['last_operations'] = True

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('user-operations-history') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            len(response.data['results']),
            2,
        )
        max_time_series = max(self.logs_series, key=operator.attrgetter['access_time'])
        max_time_seasons = max(self.logs_seasons, key=operator.attrgetter['access_time'])



