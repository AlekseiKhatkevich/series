from rest_framework import filters


class CustomSearchFilter(filters.SearchFilter):
    """
    Filter adds few new lookups to search. Used in project level settings.
    """
    lookup_prefixes = {
        '^': 'istartswith',
        '=': 'iexact',
        '@': 'search',
        '$': 'iregex',
        '%': 'trigram_similar',
        '*': 'unaccent__icontains',
    }
