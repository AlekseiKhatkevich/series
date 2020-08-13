import collections

import guardian.models
from django.db.models import F, IntegerField, functions
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from administration.helpers.initial_data import generate_changelog
from administration.models import EntriesChangeLog
from archives.models import ImageModel, SeasonModel, TvSeriesModel
from archives.tests.data import initial_data
from series import constants
from series.helpers.custom_functions import key_field_to_field_dict, response_to_dict
from users.helpers import create_test_users


class UserResourcesPositiveTest(APITestCase):
    """
    Test on user resources endpoints.
    users/entries/
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

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

        cls.image_model_name = ImageModel._meta.model_name
        cls.series_model_name = TvSeriesModel._meta.model_name
        cls.season_model_name = SeasonModel._meta.model_name
        cls.model_names = (cls.image_model_name, cls.season_model_name, cls.series_model_name,)

    def setUp(self) -> None:
        self.logs_series = generate_changelog(self.series_1, self.user_1, num_logs=6)
        self.logs_seasons = generate_changelog(self.season_1_1, self.user_1, num_logs=6)
        self.logs_images = generate_changelog(self.image_1_1, self.user_1, num_logs=6)

    def test_series(self):
        """
        Check that endpoint displays series that belong to request user.
        """
        series = self.series_1
        user = series.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['series']},
            {series.pk, },
        )
        self.assertSetEqual(
            {data['name'] for data in response.data['series']},
            {series.name, },
        )

    def test_seasons(self):
        """
        Check that endpoint displays seasons that belong to request user.
        """
        series = self.series_1
        user = series.entry_author
        seasons = self.seasons_dict[series.pk]

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['seasons']},
            {season.pk for season in seasons},
        )
        self.assertSetEqual(
            {data['series_name'] for data in response.data['seasons']},
            {series.name, },
        )
        self.assertSetEqual(
            {data['season_number'] for data in response.data['seasons']},
            {season.season_number for season in seasons},
        )

    def test_images(self):
        """
        Check that endpoint displays images that belong to request user.
        """
        series = self.series_1
        user = series.entry_author
        images = filter(lambda image: image.entry_author == user, self.images)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['images']},
            {image.pk for image in images},
        )
        self.assertSetEqual(
            {data['model'] for data in response.data['images']},
            {series.__class__._meta.model_name, },
        )
        self.assertSetEqual(
            {data['object_name'] for data in response.data['images']},
            {series.name, },
        )

    def test_user_operation_history(self):
        """
        Check that user operations history API endpoint /user-resources/operations-history/ GET
        displays user's operations history correctly.
        """
        user = self.user_1
        logs = self.logs_images + self.logs_seasons + self.logs_series
        for log in logs:
            log.state['id'] = log.pk

        EntriesChangeLog.objects.bulk_update(
            logs, ['state', ]
        )

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-operations-history'),
            data=None,
            format='json',
        )

        response_dict = response_to_dict(response, key_field='id', )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        #  Check that all entries shown in response are belong to user.
        self.assertSetEqual(
            set(response_dict.keys()),
            set(EntriesChangeLog.objects.filter(user=user).values_list('pk', flat=True)),
        )
        #  Check that model names are shown correctly.
        models = key_field_to_field_dict(response, 'id', 'model')
        cnt = collections.Counter(models.values())

        for model_name in self.model_names:
            with self.subTest(model_name=model_name):
                self.assertEqual(
                    cnt[model_name],
                    6
                )
        #  Check that difference between states is shown correctly.
        for one_log in response_dict.values():
            with self.subTest(one_log=one_log):
                diff = one_log['diff']
                if diff is not None:
                    diff_id = diff['id']
                    log_pk = one_log['id']
                    self.assertEqual(
                        diff_id,
                        log_pk - 1,
                    )

    def test_user_objects_history_endpoint(self):
        """
        Check that API endpoint /user-resources/user-objects-history/ returns only 'EntriesChangeLog'
        entries of objects that belong to request user.
        """
        second_user_logs = generate_changelog(self.series_2, self.user_2, num_logs=6)
        user = self.series_2.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-objects-history'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response_dict = response_to_dict(response, key_field='id', )

        self.assertEqual(
            len(response_dict.keys()),
            len(second_user_logs),
        )
        self.assertTrue(
            all([data['user'] == user.get_full_name() for data in response_dict.values()])
        )


class AllowedToHandleEntriesPositiveTest(APITestCase):
    """
    Test on endpoint that displays resources allowed to handle for request user.
    /user-resources/allowed-handle-entries/ GET
    """
    maxDiff = None

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

        self.images = initial_data.create_images_instances(self.series, num_img=2)
        self.image_1_1, self.image_1_2, self.image_2_1, self.image_2_2 = self.images

        self.seasons, self.seasons_dict = initial_data.create_seasons(
            self.series,
            num_seasons=3,
            return_sorted=True,
        )
        self.season_1_1, self.season_1_2, self.season_1_3, *series_2_seasons = self.seasons

    def test_endpoint_user_is_master_or_slave(self):
        """
        Check that endpoint displays only objects that are allowed for request user to be handled.
        Where user is:
        -master
        """
        user = self.user_1
        slave = self.user_2
        user.slaves.add(slave)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('allowed-handle-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for key, model in zip(
                ('series', 'seasons', 'images'),
                (TvSeriesModel, SeasonModel, ImageModel)
        ):
            with self.subTest(key=key, model=model):
                self.assertSetEqual(
                    {data['pk'] for data in response.data[key]},
                    set(model.objects.filter(entry_author=slave).values_list('pk', flat=True)),
                )

    def test_endpoint_user_is_slave(self):
        """
        Check that endpoint displays only objects that are allowed for request user to be handled.
        Where user is:
        -master
        """
        user = self.user_1
        master = self.user_2
        master.slaves.add(user)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('allowed-handle-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for key, model in zip(
                ('series', 'seasons', 'images'),
                (TvSeriesModel, SeasonModel, ImageModel)
        ):
            with self.subTest(key=key, model=model):
                self.assertSetEqual(
                    {data['pk'] for data in response.data[key]},
                    set(model.objects.filter(entry_author=master).values_list('pk', flat=True)),
                )

    def test_endpoint_user_is_friend(self):
        """
        Check that endpoint displays only objects that are allowed for request user to be handled.
        Where user is:
        - friend (has object permission on object)
        """
        user = self.user_1
        object_owner = self.user_2
        permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE

        object_owner_series = [series for series in self.series if series.entry_author == object_owner]
        object_owner_seasons = [season for season in self.seasons if season.entry_author == object_owner]
        object_owner_images = [image for image in self.images if image.entry_author == object_owner]

        for obj in (*object_owner_series, *object_owner_seasons, *object_owner_images):
            assign_perm(permission_code, user, obj)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('allowed-handle-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for key, model in zip(
                ('series', 'seasons', 'images'),
                (TvSeriesModel, SeasonModel, ImageModel)
        ):
            with self.subTest(key=key, model=model):
                self.assertSetEqual(
                    {data['pk'] for data in response.data[key]},
                    set(
                        guardian.models.UserObjectPermission.objects.filter(
                            content_type__model=model._meta.model_name,
                            content_type__app_label=model._meta.app_label,
                            user=user,
                            permission__codename=permission_code,
                        ).values_list(
                            functions.Cast(
                                F('object_pk'),
                                output_field=IntegerField()),
                            flat=True,
                        ))
                )
