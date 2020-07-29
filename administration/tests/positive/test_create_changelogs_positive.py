import datetime

from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import administration.models
import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class CreateAccessLogPositiveTest(APITestCase):
    """
    Positive test on EntriesChangeLog instances creation on series and seasons create, update, delete.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.image = initial_data.generate_test_image()

    def setUp(self) -> None:
        self.seasons = initial_data.create_seasons(self.series)
        self.season_1_1, *rest = self.seasons

        self.data = {
            'translation_years': {'lower': '2020-01-01'},
            'name': 'test-test',
            'imdb_url': 'https://www.imdb.com/',
            'interrelationship': [
                {
                    'name': self.series_1.name,
                    'reason_for_interrelationship': 'test1'
                },
                {
                    'name': self.series_2.name,
                    'reason_for_interrelationship': 'test1'
                }]}

    def test_tvseries_log_entry_created(self):
        """
        Check that 'EntriesChangeLog' instance is created along with series instance creation.
        """
        self.client.force_authenticate(user=self.user_1)

        response = self.client.post(
            reverse('tvseries'),
            data=self.data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=response.data['pk'],
                user=self.user_1,
                as_who=administration.models.UserStatusChoices.CREATOR.value,
                operation_type=administration.models.OperationTypeChoices.CREATE.value,
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ).exists()
        )

    def test_test_tvseries_log_entry_updated(self):
        """
        Check that log gets created when TvSeriesModel instance is updated via API endpoint.
        """
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=response.data['pk'],
                user=user,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.UPDATE,
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ).exists()
        )

    def test_test_tvseries_log_entry_deleted(self):
        """
        Check that log gets created when TvSeriesModel instance is deleted via API endpoint.
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

        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=self.series_1.pk,
                user=user,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.DELETE,
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ).exists()
        )

    def test_test_seasons_log_entry_created(self):
        """
        Check that log gets created when SeasonModel instance is created via API endpoint.
        """
        test_series = self.series_1
        test_series.seasons.all().delete()
        tr_lower = test_series.translation_years.lower + datetime.timedelta(days=1)
        tr_upper = test_series.translation_years.lower + datetime.timedelta(days=300)

        data = {
            'season_number': 1,
            'number_of_episodes': 10,
            'last_watched_episode': 2,
            'episodes': {
                '1': (tr_lower + datetime.timedelta(days=1)).isoformat(),
                '2': (tr_lower + datetime.timedelta(days=10)).isoformat(),
            },
            'translation_years': {
                'lower': tr_lower.isoformat(),
                'upper': tr_upper.isoformat(),
                'bounds': '[]',
            }}

        self.client.force_authenticate(user=test_series.entry_author)

        response = self.client.post(
            reverse('seasonmodel-list', args=(test_series.pk,)),
            data=data,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=response.data['pk'],
                user=test_series.entry_author,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.CREATE,
                content_type__model=archives.models.SeasonModel.__name__.lower(),
                content_type__app_label=archives.models.SeasonModel._meta.app_label.lower(),
            ).exists()
        )

    def test_test_seasons_log_entry_updated(self):
        """
        Check that log gets created when SeasonModel instance is updated via API endpoint.
        """
        test_season = self.season_1_1

        self.client.force_authenticate(user=self.season_1_1.entry_author)

        response = self.client.patch(
            test_season.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=response.data['pk'],
                user=self.season_1_1.entry_author,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.UPDATE,
                content_type__model=archives.models.SeasonModel.__name__.lower(),
                content_type__app_label=archives.models.SeasonModel._meta.app_label.lower(),
            ).exists()
        )

    @test_helpers.switch_off_validator('IsImageValidator')
    def test_create_logs_after_upload_image(self):
        """
        Check that log is created after image creation.
        """
        data = {'file': self.image}
        user = self.series_1.entry_author
        filename = 'small_image.gif'

        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse('upload', args=[self.series_1.pk, filename]),
            data=data,
            format='gif',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertTrue(
            administration.models.EntriesChangeLog.objects.filter(
                user=self.season_1_1.entry_author,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.CREATE,
                content_type__model=archives.models.ImageModel.__name__.lower(),
                content_type__app_label=archives.models.ImageModel._meta.app_label.lower(),
            ).exists()
        )


