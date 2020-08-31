from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SubtitlesModelPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on 'Subtitles' model in 'archives' app.
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

    def test_model_creation(self):
        """
        Check that if correct data provided -model instance can be successfully created.
        """
        archives.models.Subtitles.objects.create(
            **self.subtitles_data
        )
        self.assertTrue(
            archives.models.Subtitles.objects.filter(**self.subtitles_data).exists()
        )
