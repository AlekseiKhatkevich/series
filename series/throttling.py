from django.core.cache import caches
from rest_framework import throttling


class CustomScopeThrottle(throttling.ScopedRateThrottle):
    """
    Just uses separate cache.
    """
    cache = caches['throttling']