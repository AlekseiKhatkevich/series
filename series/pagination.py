import functools

from rest_framework.pagination import LimitOffsetPagination


class FasterLimitOffsetPagination(LimitOffsetPagination):

    @functools.lru_cache
    def get_count(self, queryset):
        """
        Simply evaluate qs (good for complex queries, might be faster then SQL COUNT).
        """
        return len(queryset)

