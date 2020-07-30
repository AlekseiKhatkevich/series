from django.urls import resolve
from rest_framework.reverse import reverse
from rest_framework.test import APISimpleTestCase

import archives.models


class CustomConvertersPositiveTest(APISimpleTestCase):
    """
    Positive test on administration custom path converters.
    """
    url = r'/administration/history/tvseriesmodel/158/'

    def test_ModelNameConverter_to_python(self):
        """
        Check that 'ModelNameConverter' is able to parse model name from url and convert it to actual
        model class.
        """
        resolver = resolve(self.url)

        self.assertEqual(
            resolver.url_name,
            'history-list'
        )
        self.assertEqual(
            resolver.kwargs['model_name'],
            archives.models.TvSeriesModel,
        )

    def test_ModelNameConverter_to_url(self):
        """
        Check that 'ModelNameConverter' is able to work with 'reverse'.
        """
        url = reverse('history-list', args=['tvseriesmodel', 158])

        self.assertTrue(
            url.endswith('158/')
        )


