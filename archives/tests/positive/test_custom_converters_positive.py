from rest_framework.test import APISimpleTestCase
from rest_framework.reverse import reverse
from django.urls import resolve


class CustomConvertersPositiveTest(APISimpleTestCase):
    """
    Positive test on app custom path converters.
    """
    url = r'/archives/tvseries/129/delete-image/399,331/'

    def test_comma_separated_path_converter_regex(self):
        """
        Check that 'CommaSeparatedIntegersPathConverter' path converter is able to extract parts of the url
        with comma separated string digits.
        """
        resolver = resolve(self.url)

        self.assertEqual(
            resolver.url_name,
            'delete-image'
        )
        self.assertTupleEqual(
            resolver.kwargs['image_pk'],
            (399, 331)
        )

    def test_comma_separated_path_converter_to_url(self):
        """
        Check that 'CommaSeparatedIntegersPathConverter' method 'to_url'
        returns comma separated list of string digits.
        """
        url = reverse('delete-image', args=[129, (399, 331)])
        self.assertTrue(
            url.endswith('399,331/')
        )

