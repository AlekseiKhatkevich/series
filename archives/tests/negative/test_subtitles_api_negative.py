import io
import os

from django.conf import settings
from django.core.files import File
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesAPINegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test on Subtitles  create/delete api endpoint.
    /archives/tvseries/<int:pk>/seasons/<int:pk>/add_subtitle/ POST
    /archives/tvseries/<int:pk>/seasons/<int:pk>/delete_subtitle/<int:pk>/ DELETE
    """

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

        test_srt_file_path = os.path.join(settings.MEDIA_ROOT, 'files_for_tests', 'test.srt')
        cls.srt_file = File(open(test_srt_file_path, 'r'))

    def setUp(self) -> None:
        self.data = dict(
            episode_number=1,
            language='en',
            text=self.srt_file,
        )

    def test_upload_subtitle_api_permissions(self):
        """
        Check that permissions are involved in upload.
        """
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
            status.HTTP_403_FORBIDDEN,
        )

    def test_upload_api_no_lng_can_not_determine_lng_automatically(self):
        """
        Check that if no language was provided on upload and language can;t be recognized
        automatically by some reason or another, than validation error is arisen.
        """
        expected_error_message = error_codes.LANGUAGE_UNDETECTED.message
        del self.data['language']
        undetectable_string = '#############################'
        self.data['text'] = File(io.StringIO(undetectable_string))

        self.client.force_authenticate(user=self.season_1_1.entry_author)

        response = self.client.post(
            reverse(
                'seasonmodel-add-subtitle',
                args=(self.season_1_1.series_id, self.season_1_1.pk,)
            ),
            data=self.data,
            format='multipart',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_message=expected_error_message,
            field=None,
        )

    def test_delete_subtitle_api_permissions(self):
        """
        Check that permissions are involved in delete.
        """
        response = self.client.delete(
            reverse(
                'seasonmodel-delete-subtitle',
                args=(self.season_1_3.series_id, self.season_1_3.pk, 1,)
            ),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_delete_subtitle_api_if_not_such_subtitle(self):
        """
        Check that view would raise error is pk of subtitle in url doesnt coincide
        to any pk from DB.
        """
        self.client.force_authenticate(user=self.season_1_3.entry_author)

        response = self.client.delete(
            reverse(
                'seasonmodel-delete-subtitle',
                args=(self.season_1_3.series_id, self.season_1_3.pk, 9999999999999,)
            ),
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_message=error_codes.NO_SUCH_SUBTITLE.message,
            field=None,
        )




