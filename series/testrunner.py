from django.conf import settings
from django.test.runner import DiscoverRunner


class MyTestSuiteRunner(DiscoverRunner):
    """
    Custom test runner that sets settings 'IM_IN_TEST_MODE' to True while running tests.
    """

    def setup_test_environment(self, **kwargs):
        super().setup_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = True

    def teardown_test_environment(self, **kwargs):
        super().teardown_test_environment(**kwargs)
        settings.IM_IN_TEST_MODE = False
