import ipaddress
import random
import more_itertools
import django_redis
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from django.utils import timezone
from rest_framework.test import APIRequestFactory, APITestCase

import administration.models
from administration.helpers.initial_data import generate_blacklist_ips, \
    generate_random_ip4, generate_random_ip6
from series import constants
from series.helpers.test_helpers import TestHelpers
from series.middleware import IpBlackListMiddleware


class IpBlackListMiddlewareNegativeTest(TestHelpers, APITestCase):
    """
    Negative test on 'IpBlackListMiddleware'.
    """

    maxDiff = None
    cache = caches[settings.BLACKLIST_CACHE]
    cache_key = constants.IP_BLACKLIST_CACHE_KEY

    @classmethod
    def setUpTestData(cls):
        cls.cache.delete(cls.cache_key)
        cls.redis_client = django_redis.get_redis_connection(settings.BLACKLIST_CACHE)
        cls.redis_native_cache_key = BaseCache({}).make_key(cls.cache_key)

    def setUp(self) -> None:
        self.blacklist_entries = generate_blacklist_ips(5, 5, protocols=(4, 6, ), num_networks=1)

        self.blacklist_ips = {entry.ip for entry in self.blacklist_entries}
        self.black_ip4 = more_itertools.first_true(
            self.blacklist_ips,
            lambda ip: ipaddress.ip_network(obj).version == 6, networks)
        )


        self.request_ip4 = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=self.white_ip_4,
            REMOTE_ADDR=self.white_ip_4,
        )
        self.request_ip6 = APIRequestFactory().request(
            HTTP_X_FORWARDED_FOR=self.white_ip_6,
            REMOTE_ADDR=self.white_ip_6,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.cache.delete(cls.cache_key)

    def tearDown(self) -> None:
        self.cache.delete(self.cache_key)

    def test_block_ip_direct_match(self):
        """
        Check that ip is contained in Redis blacklist ips set, than 403 response is returned.
        """
