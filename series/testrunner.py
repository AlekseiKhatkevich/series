import os
import shutil
import tempfile

from django.conf import settings
from django.test.runner import DiscoverRunner

from series.settings import MEDIA_ROOT


class MyTestSuiteRunner(DiscoverRunner):
    """
    Custom test runner that sets settings 'IM_IN_TEST_MODE' to True while running tests,
    and monkey patches MEDIA_URLto temporary directory.
    """
    original_media_root = settings.MEDIA_ROOT

    assert original_media_root == MEDIA_ROOT, 'Check MEDIA_ROOT in "settings.py" and in "testrunner.py"'

    temp_dir = None

    def setup_test_environment(self, **kwargs):
        #  Add flag 'IM_IN_TEST_MODE' into settings.
        super().setup_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = True
        #  Move 'MEDIA_ROOT' into temporary folder.
        self.temp_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.temp_dir
        #  Copy test images into aforementioned folder.
        test_images_folder = os.path.join(self.temp_dir, 'images_for_tests')
        shutil.copytree(settings.IMAGES_FOR_TESTS, test_images_folder)

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = False
        settings.MEDIA_ROOT = self.original_media_root

        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            pass

        assert settings.MEDIA_ROOT == self.original_media_root, '"MEDIA_ROOT" is corrupted.'

