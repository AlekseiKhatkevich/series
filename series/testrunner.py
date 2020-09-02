import os
import shutil
import tempfile

from django.conf import settings
from django.core.cache import caches
from django.test.runner import DiscoverRunner

from series import constants
from series.settings import MEDIA_ROOT


class MyTestSuiteRunner(DiscoverRunner):
    """
    Custom test runner that sets settings 'IM_IN_TEST_MODE' to True while running tests,
    and monkey patches MEDIA_URLto temporary directory.
    """
    original_media_root = settings.MEDIA_ROOT

    assert original_media_root == MEDIA_ROOT, 'Check MEDIA_ROOT in "settings.py" and in "testrunner.py"'

    temp_dir = None

    @staticmethod
    def remove_blacklist_key() -> None:
        """
        Removes blacklist cache key from cache.
        """
        blacklist_cache = caches[settings.BLACKLIST_CACHE]
        blacklist_cache_key = constants.IP_BLACKLIST_CACHE_KEY

        blacklist_cache.delete(blacklist_cache_key)

    def setup_test_environment(self, **kwargs):
        #  Add flag 'IM_IN_TEST_MODE' into settings.
        super().setup_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = True
        #  Move 'MEDIA_ROOT' into temporary folder.
        self.temp_dir = tempfile.mkdtemp()
        settings.MEDIA_ROOT = self.temp_dir
        #  Copy test images and files into aforementioned folder.
        test_images_folder = os.path.join(self.temp_dir, 'images_for_tests')
        test_files_folder = os.path.join(self.temp_dir, 'files_for_tests')
        shutil.copytree(settings.IMAGES_FOR_TESTS, test_images_folder)
        shutil.copytree(settings.FILES_FOR_TESTS, test_files_folder)
        #  Clean blacklist cache.
        self.remove_blacklist_key()

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = False
        settings.MEDIA_ROOT = self.original_media_root

        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            pass

        assert settings.MEDIA_ROOT == self.original_media_root, '"MEDIA_ROOT" is corrupted.'

        #  Clean blacklist cache.
        self.remove_blacklist_key()

