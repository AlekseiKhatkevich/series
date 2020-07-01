import operator

from guardian.shortcuts import assign_perm, get_users_with_perms
from rest_framework import status
from rest_framework.test import APITestCase

import archives.models
import series.constants
from archives.tests.data import initial_data
from users.helpers import create_test_users


class TvSeriesDetailUpdateDeletePositiveTest(APITestCase):
    """
    Positive test on detail/ update/ delete action on TvSeries model instances via API endpoint:
    /archives/tvseries/<series_pk>/ GET, PUT, PATCH.
    """

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series
        self.series_1.interrelationship.add(self.series_2)

        initial_data.create_images_instances((self.series_1,))

        self.seasons = initial_data.create_seasons(self.series)
        self.season_of_series_1, *_, self.season_of_series_2, = \
            sorted(self.seasons, key=operator.attrgetter('series_id'))

        self.series_1_number_of_episodes = sum(
            (season.number_of_episodes for season in self.seasons if season.series == self.series_1)
        )

    def test_detail_view(self):
        """
        Check that detail action works correct.
        """
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        for field in ('pk', 'name', 'imdb_url', 'is_finished', 'rating',):
            with self.subTest(field=field):
                self.assertEqual(
                    getattr(self.series_1, field),
                    response.data[field],
                )
        self.assertEqual(
            self.series_1.entry_author.get_full_name(),
            response.data['entry_author']
        )
        self.assertEqual(
            self.series_1.interrelationship.first().name,
            self.series_2.name
        )
        self.assertEqual(
            self.series_1.seasons.all().count(),
            response.data['number_of_seasons']
        )
        self.assertEqual(
            self.series_1_number_of_episodes,
            response.data['number_of_episodes'],
        )
        self.assertEqual(
            self.series_1.images.first().image.url.split('/')[-1],
            response.data['images'][0]['image'].split('/')[-1],
        )
        self.assertSequenceEqual(
            [
                {'pk': elem['pk'], 'season_number': elem['season_number']}
                for elem in self.series_1.seasons.all().values('pk', 'season_number')
            ],
            response.data['seasons'],
        )

    def test_allowed_redactors(self):
        """
        Check whether field 'allowed_redactors' represents allowed redactors of the object correctly.
        """
        user = self.series_1.entry_author
        self.user_2.slaves.add(user)
        user.slaves.add(self.user_3)
        assign_perm(series.constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE, self.user_3, self.series_1)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertDictEqual(
            {'pk': user.master_id, 'name': user.master.get_full_name()},
            response.data['allowed_redactors']['master'],
        )
        self.assertListEqual(
            [{'pk': user.slaves.first().pk, 'name': user.slaves.first().get_full_name()}],
            response.data['allowed_redactors']['slaves'],
        )
        self.assertListEqual(
            [
                {'friend_full_name': user.get_full_name(), 'friend_pk': user.pk}
                for user in get_users_with_perms(
                    self.series_1,
                    with_group_users=False,
                    only_with_perms_in=(series.constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE,),
                    )],
            list(response.data['allowed_redactors']['friends'])
        )

    def test_update(self):
        """
        Check that model instance can be successfully updated.
        """
        data = {
            'translation_years': {'lower': '2012-01-01'},
            'name': 'test_updated',
            'imdb_url': 'https://www.imdb.com/name/nm3929195/',
            'rating': 7,
            'interrelationship': [
                {
                    'name': self.series_2.name,
                    'reason_for_interrelationship': 'test_updated',
                }]}
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.put(
            self.series_1.get_absolute_url,
            data=data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            self.series_1,
            self.series_1.refresh_from_db(),
        )
        self.assertEqual(
            self.series_1.group.get(to_series=self.series_2.pk).reason_for_interrelationship,
            'test_updated',
        )

    def test_delete_interrelationship(self):
        """
        Check that interrelationships can be deleted.
        """
        data = {'interrelationship': []}
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.series_1.get_absolute_url,
            data=data,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertFalse(
            self.series_1.interrelationship.all().exists()
        )

    def test_delete_series(self):
        """
        Check that series can be successfully deleted.
        """
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.delete(
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
           archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk).exists()
        )
