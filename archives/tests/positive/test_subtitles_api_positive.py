import os

from django.conf import settings
from django.core.files import File
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesAPIPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on Subtitles  create/delete api endpoint.
    /archives/tvseries/<int:pk>/seasons/<int:pk>/add_subtitle/ POST
    /archives/tvseries/<int:pk>/seasons/<int:pk>/delete_subtitle/<int:pk>/ DELETE
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.seasons, cls.seasons_dict = initial_data.create_seasons(
            cls.series,
            num_seasons=3,
            return_sorted=True,
        )
        cls.season_1_1, cls.season_1_2, cls.season_1_3, *series_2_seasons = cls.seasons

    def tearDown(self) -> None:
        self.srt_file.close()

    def setUp(self) -> None:
        test_srt_file_path = os.path.join(settings.MEDIA_ROOT, 'files_for_tests', 'test.srt')
        self.srt_file = File(open(test_srt_file_path, 'r'))

        self.data = dict(
            episode_number=1,
            language='en',
            text=self.srt_file,
        )

    def test_upload_subtitle(self):
        """
        Check that subtitles upload api works correctly.
        """

        self.client.force_authenticate(user=self.season_1_1.entry_author)

        response = self.client.post(
            reverse(
                'seasonmodel-add-subtitle',
                args=(self.season_1_1.series_id, self.season_1_1.pk,)
            ),
            data=self.data,
            format='multipart',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            archives.models.Subtitles.objects.filter(
                season=self.season_1_1,
                episode_number=self.data['episode_number'],
                language=self.data['language'],
            ).exists()
        )
        self.assertGreater(
            len(archives.models.Subtitles.objects.first().text),
            0,
        )

    def test_upload_subtitle_without_language(self):
        """
        Check that subtitles upload api figures out language automatically if language
        wasn't specified on upload.
        """
        del self.data['language']

        self.client.force_authenticate(user=self.season_1_1.entry_author)

        response = self.client.post(
            reverse(
                'seasonmodel-add-subtitle',
                args=(self.season_1_1.series_id, self.season_1_1.pk,)
            ),
            data=self.data,
            format='multipart',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(
            archives.models.Subtitles.objects.first().language,
            'en',
        )

    def test_delete_subtitle(self):
        """
        Check that api can delete chosen subtitle entry from DB.
        """
        subtitle = archives.models.Subtitles.objects.create(
            season=self.season_1_3,
            **self.data,
        )
        self.client.force_authenticate(user=self.season_1_3.entry_author)

        response = self.client.delete(
            reverse(
                'seasonmodel-delete-subtitle',
                args=(self.season_1_3.series_id, self.season_1_3.pk, subtitle.pk,)
            ),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            archives.models.Subtitles.objects.filter(pk=subtitle.pk).exists()
        )

