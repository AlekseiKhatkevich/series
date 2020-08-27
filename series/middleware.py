import datetime
import functools
import ipaddress
from numbers import Integral
from typing import Set, Tuple

import django_redis
from django.conf import settings
from django.contrib.postgres.aggregates import ArrayAgg
from django.core.cache import caches
from django.core.cache.backends.base import BaseCache
from django.db.models import DateTimeField, ExpressionWrapper, F, Min
from django.db.models.functions import Coalesce, Now
from django.http import HttpRequest, JsonResponse
from rest_framework import status, throttling

import administration.models
from series import constants


class IpBlackListMiddleware:
    """
    Declines request if ip address is in blacklist.
    """
    cache = caches[settings.BLACKLIST_CACHE]
    default_cache_ttl = datetime.timedelta(days=1)
    cache_key = constants.IP_BLACKLIST_CACHE_KEY
    model = administration.models.IpBlacklist
    sentinel = 'SENTINEL'

    # Class variables for native Redis ip in blacklisted ips check.
    redis_client = django_redis.get_redis_connection(settings.BLACKLIST_CACHE)
    redis_native_cache_key = BaseCache({}).make_key(cache_key)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_ip_address(request)
        ip_set = self.prepare_ip_address(ip, bits_down=8)
        is_blacklisted = self.is_ip_blacklisted(ip_set)

        if is_blacklisted:
            return JsonResponse({
                'state': 'Forbidden',
                'reason': f'IP address {ip} is within api blacklist.',
                'status': status.HTTP_403_FORBIDDEN,
            }, status=status.HTTP_403_FORBIDDEN,
            )
        else:
            return self.get_response(request)

    @staticmethod
    def get_ip_address(request: HttpRequest) -> str:
        """
        Fetches user ip address from request.
        """
        return throttling.BaseThrottle().get_ident(request)

    @staticmethod
    @functools.lru_cache(maxsize=1000, )
    def prepare_ip_address(ip: str, bits_down: int) -> Set[str]:
        """
        Returns set of ips address itself and it's supernets down to min_bit where
        this ip might be located.
        ['228.228.228.200/31', '228.228.228.200/30', '228.228.228.200/29',
        '228.228.228.192/28', '228.228.228.192/27',
        '228.228.228.192/26', '228.228.228.128/25', '228.228.228.0/24']
        + ip address itself for '228.228.228.200'
        In other words - all nets where this exact ip can be inside.
        """
        ip_obj = ipaddress.ip_network(ip)
        #  Bit masks -- 32-24 for ipv4; 128-120 for ipv6 if bits_down == 8.
        supernets_range = range(1, bits_down + 1)
        supernets = set(
            ip_obj.supernet(prefixlen_diff=step).compressed for step in supernets_range
        )
        supernets.add(ip)

        return supernets

    def get_blacklisted_ips_from_db(self) -> Tuple[set, Integral]:
        """
        Fetches blacklisted ips from database. Returns set of blacklisted ips and minimal
        time left to ips being liberated from blacklist. This time should be used as cache ttl
        lately.
        """
        elapsed_time_to_lock_release = ExpressionWrapper(
            (F('record_time') + F('stretch')), output_field=DateTimeField()) - Now()

        blacklist_entries = self.model.objects.only_active().aggregate(
            ttl=Coalesce(Min(elapsed_time_to_lock_release), self.default_cache_ttl),
            ips=ArrayAgg('ip'),
        )

        return blacklist_entries['ips'], blacklist_entries['ttl'].total_seconds()

    def is_ip_blacklisted(self, ips_set: set) -> bool:
        """
        Checks whether ip is blacklisted inside cache without pulling data from cache.
        """
        pipe = self.redis_client.pipeline()

        # if key is not exists -fetch ips from db and set them in Redis.
        if not self.redis_client.exists(self.redis_native_cache_key):

            ips_to_write, ttl = self.get_blacklisted_ips_from_db()
            # if there are no any ips in DB we create empty set(set with sentinel).
            if not ips_to_write:
                ips_to_write = (self.sentinel, )

            pipe.sadd(
                self.redis_native_cache_key,
                *ips_to_write,
            ).expire(
                self.redis_native_cache_key,
                time=int(ttl),
            ).execute()

            return not ips_set.isdisjoint(ips_to_write)

        # If key exists check if our ip and networks are in cache blacklist.
        else:
            for ip in ips_set:
                pipe.sismember(
                    self.redis_native_cache_key,
                    ip,
                )
            result = pipe.execute()

            return any(result)
