from djoser.conf import settings as djoser_settings
from rest_framework.test import APISimpleTestCase

from users.helpers.context_managers import OverrideDjoserSetting


class ContextManagersPositiveTest(APISimpleTestCase):
    """
    Test on custom context managers.
    """

    def test_DjoserSettingOverride_context_manager(self):
        """
        Check that 'OverrideDjoserSetting' context manager overrides given setting inside self.
        """
        original_value = djoser_settings.SEND_ACTIVATION_EMAIL
        overridden_value = not original_value

        with OverrideDjoserSetting(SEND_ACTIVATION_EMAIL=overridden_value):
            self.assertEqual(
                djoser_settings.SEND_ACTIVATION_EMAIL,
                not original_value
            )

        self.assertEqual(
            djoser_settings.SEND_ACTIVATION_EMAIL,
            original_value
        )