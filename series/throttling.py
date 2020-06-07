from django.core.cache import caches
from rest_framework import throttling


class CustomScopeThrottle(throttling.ScopedRateThrottle):
    cache = caches['throttling']