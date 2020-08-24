import random
from django.core.cache.backends.base import BaseCache
import django_redis
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import caches
from rest_framework.test import APIRequestFactory, APITestCase
from django.utils import timezone
from administration.helpers.initial_data import generate_blacklist_ips, generate_random_ip4
from series import constants
from series.middleware import IpBlackListMiddleware
import unittest


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

        cls.request = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=cls.white_ip,
            REMOTE_ADDR=cls.white_ip,
        )
        cls.redis_client = django_redis.get_redis_connection(settings.BLACKLIST_CACHE)
        cls.redis_native_cache_key = BaseCache({}).make_key(cls.cache_key)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.cache.delete(cls.cache_key)

    def test_grant_access_on_whitelist_ip(self):
        """
        Check that if ip not in blacklist than access is granted and request precedes to a next
        middleware.
        """
        response = IpBlackListMiddleware(get_response=SessionMiddleware)(self.request)

        self.assertIsInstance(
            response,
            SessionMiddleware,
        )

    @unittest.skip('native redis ip check is used')
    def test_key_set_in_cache(self):
        """
        Check that blacklist key and set of blacklisted ip addresses are set in cache.
        """
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request)

        self.assertSetEqual(
            self.cache.get(self.cache_key),
            self.blacklist_ips,
        )

    def test_key_set_in_cache_native(self):
        """
        Check that blacklist key and set of blacklisted ip addresses are set in cache.
        """
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request)
        raw_ips_set = self.redis_client.smembers(self.redis_native_cache_key)

        self.assertSetEqual(
            raw_ips_set,
            set(ip.encode() for ip in self.blacklist_ips),
        )

    def test_cache_ttl(self):
        """
        Check that cache ttl is equal to min. time delta until ip is released from blacklist among
        all active blacklist entries.
        """
        min_ttl = min(
            (entry.record_time + entry.stretch) - timezone.now() for entry in self.blacklist_entries
        )