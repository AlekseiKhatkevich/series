from rest_framework.test import APITestCase

from archives import models
from series.helpers.context_managers import OverrideModelAttributes


class OverrideModelAttributesContextManagerPositiveTest(APITestCase):
    """
    Test correct work of 'OverrideModelAttributes' context manager. This manager should override
    model attributes and then return them to a previous state.
    """
    fixtures = ('series.json', 'users.json')

    def test_override_model_attribute(self):
        """
        in this test we will try to turn 'is_finished' field's default=False attribute to a test value
         and then check whether  it has been returned to it's original value.
        """
        with OverrideModelAttributes(
            model=models.TvSeriesModel,
            field='is_finished',
            default='test',
        ):
            self.assertEqual(
                models.TvSeriesModel._meta.get_field('is_finished').default,
                'test',
            )
        self.assertEqual(
            models.TvSeriesModel._meta.get_field('is_finished').default,
            False,
        )

