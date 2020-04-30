from rest_framework.test import APISimpleTestCase


class TestCustomTestRunnerPositiveTest(APISimpleTestCase):
    """
    Test whether or not our custom TestRunner adds 'IM_IN_TEST_MODE = True' while tests are running.
    """

    def test_IM_IN_TEST_MODE(self):
        """
        Check if 'IM_IN_TEST_MODE = True' while we are in the test mode.
        """
        from django.conf import settings

        self.assertTrue(
           settings.IM_IN_TEST_MODE
        )