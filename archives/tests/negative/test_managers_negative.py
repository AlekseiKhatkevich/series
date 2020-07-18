from rest_framework.test import APITestCase

import archives.models
from series import error_codes


class ManagersNegativeTest(APITestCase):
    """
    Test for managers and queryset custom methods in 'archives' app.
    """
    fixtures = ('users.json', 'series.json',)

    def test_select_x_percent(self):
        """
        Check that 'select_x_percent' raises error in case 'position' argument not
        'top' or 'bottom'.
        """
        expected_error_message = error_codes.SELECT_X_PERCENT.message

        with self.assertRaisesMessage(ValueError, expected_error_message):
            archives.models.TvSeriesModel.objects.all().select_x_percent(66, 'test')
