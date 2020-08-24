import datetime
import ipaddress
import itertools
from numbers import Integral
from typing import Tuple

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
    Declines request if ip address in blacklist.
    """
    cache = caches[settings.BLACKLIST_CACHE]
    cache_ttl = datetime.timedelta(days=1)
    cache_key = constants.IP_BLACKLIST_CACHE_KEY
    model = administration.models.IpBlacklist

    # Class variables for native Redis ip in blacklisted ips check.
    redis_client = django_redis.get_redis_connection(settings.BLACKLIST_CACHE)
    redis_native_cache_key = BaseCache({}).make_key(cache_key)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_ip_address(request)
        #is_blacklisted = self.is_ip_blacklisted(ip)
        is_blacklisted = self.is_ip_blacklisted_native_version(ip)
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

    def get_blacklisted_ips_from_db(self) -> Tuple[set, Integral]:
        """
        Fetches blacklisted ips from database. Returns set of blacklisted ips and minimal
        time left to ip being liberated from blacklist. This time should be used as cache ttl
        lately.
        """
        elapsed_time_to_lock_release = ExpressionWrapper(
                 (F('record_time') + F('stretch')), output_field=DateTimeField()) - Now()

        blacklist_entries = self.model.objects.only_active().aggregate(
            ttl=Coalesce(Min(elapsed_time_to_lock_release), self.cache_ttl),
            ips=ArrayAgg('ip'),
        )

        #return set(blacklist_entries['ips']), blacklist_entries['ttl'].total_seconds()
        return blacklist_entries['ips'], blacklist_entries['ttl'].total_seconds()

    def is_ip_blacklisted(self, ip: str) -> bool:
        """
        Checks whether IP blacklisted.
        """
        ips_from_cache = self.cache.get(key=self.cache_key)

        if ips_from_cache is None:
            ips_to_write, ttl = self.get_blacklisted_ips_from_db()
            self.cache.set(
                key=self.cache_key,
                timeout=ttl,
                value=ips_to_write,
            )
            ips_from_cache = ips_to_write

        return ip in ips_from_cache

    def is_ip_blacklisted_native_version(self, ip: str) -> bool:
        """
        Checks whether ip is blacklisted inside cache without pulling data from cache.
        """
        ip = ipaddress.ip_address(ip)

        is_key_exists = self.redis_client.exists(self.redis_native_cache_key)

        if not is_key_exists:

            ips_to_write, ttl = self.get_blacklisted_ips_from_db()
            ips_to_write = itertools.chain.from_iterable(
                ipaddress.ip_network(ip_or_net) for ip_or_net in ips_to_write
            )
            with self.redis_client.pipeline():
                self.redis_client.sadd(
                    self.redis_native_cache_key,
                    *ips_to_write,
                )
                self.redis_client.expire(
                    self.redis_native_cache_key,
                    time=int(ttl),
                )

            return ip in ips_to_write

        else:
            is_blacklisted = self.redis_client.sismember(
                self.redis_native_cache_key,
                ip,
            )

            return bool(is_blacklisted)
