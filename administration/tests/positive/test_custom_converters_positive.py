from django.urls import resolve
from rest_framework.reverse import reverse
from rest_framework.test import APISimpleTestCase

import archives.models


class CustomConvertersPositiveTest(APISimpleTestCase):
    """
    Positive test on administration custom path converters.
    """

    def test_ModelNameConverter_to_python(self):
        """
        Check that 'ModelNameConverter' is able to parse model name from url.
        """
        url_series = r'/administration/history/tvseriesmodel/158/'
        url_images = r'/administration/history/imagemodel/158/'
        url_seasons = r'/administration/history/seasonmodel/158/'

        for url, model_type in zip(
                (url_series, url_images, url_seasons),
                (archives.models.TvSeriesModel, archives.models.ImageModel, archives.models.SeasonModel),
        ):
            with self.subTest(url=url, model_type=model_type):
                resolver = resolve(url)

                self.assertEqual(
                    resolver.url_name,
                    'history-list',
                )

    def test_ModelNameConverter_to_url(self):
        """
        Check that 'ModelNameConverter' is able to work with 'reverse'.
        """
        url = reverse('history-list', args=['tvseriesmodel', 158])

        self.assertTrue(
            url.endswith('158/')
        )


