import random

from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import caches
from rest_framework.test import APIRequestFactory, APITestCase

from administration.helpers.initial_data import generate_blacklist_ips, generate_random_ip4
from series import constants
from series.middleware import IpBlackListMiddleware


class IpBlackListMiddlewarePositiveTest(APITestCase):
    """
    Positive test on 'IpBlackListMiddleware'.
    """

    maxDiff = None
    cache = caches[settings.BLACKLIST_CACHE]
    cache_key = constants.IP_BLACKLIST_CACHE_KEY

    @classmethod
    def setUpTestData(cls):
        cls.cache.delete(cls.cache_key)

        cls.blacklist_entries = generate_blacklist_ips(5, 5)
        cls.blacklist_ips = {entry.ip for entry in cls.blacklist_entries}
        # Make sure that whitelist ips not in the blacklist ips.
        cls.whitelist_ips = {generate_random_ip4() for _ in range(3)}.difference(cls.blacklist_ips)

        [cls.white_ip] = random.sample(cls.whitelist_ips, 1)
        [cls.black_ip] = random.sample(cls.blacklist_ips, 1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.cache.delete(cls.cache_key)

    def test_grant_access_on_whitelist_ip(self):
        """
        Check that if ip not in blacklist than access is granted and request precedes to a next
        middleware.
        """
        request = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=self.white_ip,
            REMOTE_ADDR=self.white_ip,
        )
        response = IpBlackListMiddleware(get_response=SessionMiddleware)(request)

        self.assertIsInstance(
            response,
            SessionMiddleware,
        )

    def test_key_set_in_cache(self):
        """
        Check that blacklist key and set of blacklisted ip addresses are set in cache.
        """
        self.assertSetEqual(
            self.cache.get(self.cache_key),
            self.blacklist_ips,
        )