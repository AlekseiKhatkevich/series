import os

from django.conf import settings
from rest_framework.test import APISimpleTestCase


class TestCustomTestRunnerPositiveTest(APISimpleTestCase):
    """
    Test whether or not our custom TestRunner adds 'IM_IN_TEST_MODE = True' while tests are running.
    """

    def test_IM_IN_TEST_MODE(self):
        """
        Check if 'IM_IN_TEST_MODE = True' while we are in the test mode.
        """

        self.assertTrue(
            settings.IM_IN_TEST_MODE
        )

    def test_temporary_media_root(self):
        """
        Check that during test run MEDIA_ROOT is a temporary directory but not a MEDIA_ROOT from
        settings.py.
        """
        from series.settings import MEDIA_ROOT_FULL_PATH

        self.assertNotEqual(
            os.path.normpath(settings.MEDIA_ROOT),
            os.path.normpath(MEDIA_ROOT_FULL_PATH),
        )

    def test_test_files_copied_to_fake_media_url(self):
        """
        Check that test files (images, etc) are copied to fake temporary MEDIA_ROOT during tests.
        """
        images_folder = os.path.join(settings.MEDIA_ROOT, 'images_for_tests', )
        other_files_folder = os.path.join(settings.MEDIA_ROOT, 'files_for_tests', )

        for folder in (images_folder, other_files_folder):
            with self.subTest(folder=folder):

                self.assertTrue(
                    os.path.exists(folder)
                )
                self.assertGreaterEqual(
                    len(os.listdir(folder)),
                    1,
                )

