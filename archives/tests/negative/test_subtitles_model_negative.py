from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesModelNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test case on 'Subtitles' model in 'archives' app.
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

    def setUp(self) -> None:
        self.subtitles_data = dict(
            season=self.season_1_1,
            episode_number=1,
            text='test',
            language='en',
        )

    def test_lng_check_constraint(self):
        """
        Check that 'lng_check' check constraint would not allow to save any language code that does not
        belong to iso_639
        """
        self.subtitles_data['language'] = 'xx'
        expected_error_message = 'lng_check'

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            subtitle = archives.models.Subtitles(**self.subtitles_data)
            subtitle.save(fc=False)

    def test_clean_episode_number_gt_season_episode_number(self):
        """
        Check that it is not allowed by model clean() method to save instances where
        'episode_number' fields value is greater then correspondent series 'number_of_episodes'
        field's value.
        """
        self.subtitles_data['episode_number'] = self.season_1_1.number_of_episodes + 1
        expected_error_message = error_codes.SUB_EPISODE_NUM_GT_SEASON_EPISODE_NUM.message

        with self.assertRaisesMessage(ValidationError, expected_error_message):
            subtitle = archives.models.Subtitles(**self.subtitles_data)
            subtitle.save()

