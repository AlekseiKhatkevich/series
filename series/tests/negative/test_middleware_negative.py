import ipaddress
import json
import random

import more_itertools
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.cache import caches
from rest_framework import status
from rest_framework.test import APIRequestFactory, APITestCase

from administration.helpers.initial_data import generate_blacklist_ips
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
        cls.middleware = IpBlackListMiddleware(get_response=SessionMiddleware)

        cls.blacklist_entries = generate_blacklist_ips(5, 5, protocols=(4, 6,), num_networks=1)

        cls.blacklist_ips = {entry.ip for entry in cls.blacklist_entries}
        cls.black_ip4 = more_itertools.first_true(
            cls.blacklist_ips,
            pred=lambda ip: (ip_obj := ipaddress.ip_network(ip)).version == 4 and
            ip_obj.prefixlen == ip_obj.max_prefixlen,
        )
        cls.black_ip6 = more_itertools.first_true(
            cls.blacklist_ips,
            pred=lambda ip: (ip_obj := ipaddress.ip_network(ip)).version == 6 and
            ip_obj.prefixlen == ip_obj.max_prefixlen,
        )
        cls.black_net4 = more_itertools.first_true(
            cls.blacklist_ips,
            pred=lambda ip: (ip_obj := ipaddress.ip_network(ip)).version == 4 and
            ip_obj.prefixlen != ip_obj.max_prefixlen,
        )
        cls.black_net6 = more_itertools.first_true(
            cls.blacklist_ips,
            pred=lambda ip: (ip_obj := ipaddress.ip_network(ip)).version == 6 and
            ip_obj.prefixlen != ip_obj.max_prefixlen,
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
        for ip in (self.black_ip4, self.black_ip6):
            with self.subTest(ip=ip):
                request = APIRequestFactory().request(
                    HTTP_X_FORWARDED_FOR=ip,
                    REMOTE_ADDR=ip,
                )
                response = self.middleware(request)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                )
                response.data = json.loads(response.content)
                expected_response_data = {
                    'state': 'Forbidden',
                    'reason': f'IP address {ip} is within api blacklist.',
                    'status': status.HTTP_403_FORBIDDEN,
                }
                self.assertDictEqual(
                    expected_response_data,
                    response.data,
                )

    def test_ip_in_blacklisted_network(self):
        """
        Check that if ip in blacklisted network, than 403 response is returned.
        """
        for net in (self.black_net4, self.black_net6, ):
            with self.subTest(net=net):
                random_ip_in_net = random.choice([*ipaddress.ip_network(net)]).compressed

                request = APIRequestFactory().request(
                    HTTP_X_FORWARDED_FOR=random_ip_in_net,
                    REMOTE_ADDR=random_ip_in_net,
                )
                response = self.middleware(request)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_403_FORBIDDEN,
                )

