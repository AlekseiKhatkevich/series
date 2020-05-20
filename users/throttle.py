import random

from rest_framework import throttling

#  https://www.django-rest-framework.org/api-guide/throttling/
class RandomRateThrottle(throttling.BaseThrottle):
    def allow_request(self, request, view):
        return random.randint(1, 10) != 1