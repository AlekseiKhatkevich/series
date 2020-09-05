import functools
from unittest.mock import patch

from django.db import connection
from rest_framework.test import APITestCase

import archives.managers
import archives.models
import archives.signals
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class ArchivesSignalsPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on signals in 'archives' app.
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
            text='A fat cat sat on a mat and ate a fat rat',
            language='en',
        )
        self.subtitle = archives.models.Subtitles(**self.subtitles_data)

    @functools.lru_cache
    def get_search_vector(self, regconfig: str, text: str) -> str:
        """
        Returns result of 'to_tsvector()' Postgres function.
        """
        with connection.cursor() as cursor:
            cursor.execute(f"""SELECT to_tsvector('{regconfig}', '{text}');""")
            [search_vector] = cursor.fetchone()

        return search_vector

    def test_generate_lexemes_signal_handler(self):
        """
        Check 'generate_lexemes' populates field 'full_text' of 'Subtitles' model with lexemes.
        """
        handler = archives.signals.generate_lexemes
        self.subtitle.full_text = 'sentinel'
        self.subtitle.save()

        self.subtitle.refresh_from_db()

        self.assertEqual(
            self.subtitle.full_text,
            "'sentinel'",
        )

        self.subtitle.full_text = None
        handler(sender=archives.models.Subtitles, instance=self.subtitle)

        self.subtitle.refresh_from_db()

        self.assertEqual(
            self.subtitle.full_text,
            self.get_search_vector(
                regconfig='english',
                text='A fat cat sat on a mat and ate a fat rat',
            ))

    def test_test_generate_lexemes_signal_handler_language_in_analyzers_preferences(self):
        """
        Check 'generate_lexemes' populates field 'full_text' of 'Subtitles' model with lexemes, and
        fetches proper regconfig from analyzers_preferences in model's manager if instance
        language is specified there.
        """
        mocked_analyzers_preferences = {'en': 'english_hunspell'}
        self.subtitle.full_text = 'sentinel'
        self.subtitle.save()

        with patch.object(
                archives.managers.SubtitlesManager,
                'analyzers_preferences',
                mocked_analyzers_preferences,
        ):
            self.assertEqual(
                archives.models.Subtitles.objects.analyzers_preferences,
                mocked_analyzers_preferences,
            )
            self.subtitle.full_text = None
            handler = archives.signals.generate_lexemes
            handler(sender=archives.models.Subtitles, instance=self.subtitle)

        self.subtitle.refresh_from_db()

        self.assertEqual(
            self.subtitle.full_text,
            self.get_search_vector(
                regconfig='english_hunspell',
                text='A fat cat sat on a mat and ate a fat rat',
            ))

    def test_test_generate_lexemes_signal_handler_language_is_not_in_analyzers(self):
        """
        Check 'generate_lexemes' populates field 'full_text' of 'Subtitles' model with lexemes, and
        fetches 'simple' regconfig if model instance's language tot in available regconfigs.
        """
        self.subtitle.full_text = 'sentinel'
        self.subtitle.language = 'sq'
        self.subtitle.save()

        self.subtitle.full_text = None
        handler = archives.signals.generate_lexemes
        handler(sender=archives.models.Subtitles, instance=self.subtitle)

        self.subtitle.refresh_from_db()

        self.assertEqual(
            self.subtitle.full_text,
            self.get_search_vector(
                regconfig='simple',
                text='A fat cat sat on a mat and ate a fat rat',
            ))
