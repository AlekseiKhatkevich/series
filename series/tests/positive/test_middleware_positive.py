import ipaddress
import random

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


class IpBlackListMiddlewarePositiveTest(TestHelpers, APITestCase):
    """
    Positive test on 'IpBlackListMiddleware'.
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

        # Make sure that whitelist ips not in the blacklist ips.
        self.whitelist_ips_v4 = {generate_random_ip4() for _ in range(3)}.difference(self.blacklist_ips)
        self.whitelist_ips_v6 = {generate_random_ip6() for _ in range(3)}.difference(self.blacklist_ips)

        [self.white_ip_4] = random.sample(self.whitelist_ips_v4, 1)
        [self.white_ip_6] = random.sample(self.whitelist_ips_v6, 1)

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

    def test_grant_access_on_whitelist_ip(self):
        """
        Check that if ip not in blacklist than access is granted and request precedes to a next
        middleware.
        """
        for request_type in (self.request_ip4, self.request_ip6):
            with self.subTest(request_type=request_type):
                response = IpBlackListMiddleware(get_response=SessionMiddleware)(request_type)

        self.assertIsInstance(
            response,
            SessionMiddleware,
        )

    def test_key_set_in_cache_native(self):
        """
        Check that blacklist key and set of blacklisted ip addresses are set in cache.
        """
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip4)
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
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip6)

        min_ttl = min(
            (entry.record_time + entry.stretch) - timezone.now() for entry in self.blacklist_entries
        )
        cache_ttl = self.redis_client.ttl(self.redis_native_cache_key)
        # noinspection PyTypeChecker
        self.assertAlmostEqual(
            min_ttl,
            timezone.timedelta(seconds=cache_ttl),
            delta=timezone.timedelta(seconds=1),
        )

    def test_prepare_ip_address(self):
        """
        Check that 'prepare_ip_address' methods returns 8 supernets from 31 to 24 bit mask.
        """
        for ip in (self.white_ip_4, self.white_ip_6):
            with self.subTest(ip=ip):
                supernets = IpBlackListMiddleware(
                    get_response=SessionMiddleware
                ).prepare_ip_address(
                    ip, bits_down=8
                )

                self.assertEqual(
                    len(supernets),
                    8 + 1,
                )
                for net in supernets:
                    with self.subTest(net=net):
                        self.assertIn(
                            ipaddress.ip_address(ip),
                            ipaddress.ip_network(net),
                        )

    def test_cache_key_create_if_not_exists(self):
        """
        Check that if cache key is not exists in Redis - it will be created on first middleware call.
        """
        self.cache.delete(self.cache_key)
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip4)

        self.assertTrue(
            self.redis_client.exists(self.redis_native_cache_key)
        )

    def test_no_ips_entries(self):
        """
        Check that if there are no any active blacklist ip entries in DB, then sentinel value and default
        TTl would be written in Redis.
        """
        administration.models.IpBlacklist.objects.all().delete()
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip4)
        cache_ttl = self.redis_client.ttl(self.redis_native_cache_key)
        raw_ips_set = self.redis_client.smembers(self.redis_native_cache_key)

        # noinspection PyTypeChecker
        self.assertAlmostEqual(
            IpBlackListMiddleware.default_cache_ttl,
            timezone.timedelta(seconds=cache_ttl),
            delta=timezone.timedelta(seconds=1),
        )
        self.assertSetEqual(
            raw_ips_set,
            {IpBlackListMiddleware.sentinel.encode(), }
        )

    def test_key_already_exists(self):
        """
        Check that if cache key already exists, than ip checked only with Redis call.
        """
        # Create cache key with first call.
        IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip4)

        with self.assertNumQueries(0):
            IpBlackListMiddleware(get_response=SessionMiddleware)(self.request_ip4)

