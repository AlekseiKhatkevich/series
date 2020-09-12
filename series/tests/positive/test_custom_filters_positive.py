from rest_framework.test import APISimpleTestCase

from series import filters


class CustomFiltersPositiveTest(APISimpleTestCase):
    """
    Test for custom project level filters.
    """
    search_filter = filters.CustomSearchFilter()
    field_name = 'test'

    def test_trigram_similar_and_unaccent_lookup(self):
        """
        Check that search filter allows to use 'trigram_similar' and 'unaccent' search.
        """
        trigram_lookup_symbol = '%'
        unaccent_lookup_symbol = '*'

        for lookup_symbol in (trigram_lookup_symbol, unaccent_lookup_symbol):
            with self.subTest(lookup_symbol=lookup_symbol):
                expected_field_and_lookup = f'{self.field_name}__{self.search_filter.lookup_prefixes[lookup_symbol]}'

                self.assertEqual(
                    self.search_filter.construct_search(f'{lookup_symbol}{self.field_name}'),
                    expected_field_and_lookup,
                )

