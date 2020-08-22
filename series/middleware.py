import datetime
import operator
from typing import Tuple

from django.conf import settings
from django.core.cache import caches
from django.db.models import DateTimeField, ExpressionWrapper, F
from django.db.models.functions import Now
from django.http import HttpRequest
from rest_framework import throttling

import administration.models
from series import constants


class IpBlackListMiddleware:
    """
    Declines request if ip address in blacklist.
    """
    cache = caches[settings.BLACKLIST_CACHE]
    cache_ttl = 60 * 60 * 24
    cache_key = constants.IP_BLACKLIST_CACHE_KEY
    model = administration.models.IpBlacklist

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        ip = self.get_ip_address(request)

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    @staticmethod
    def get_ip_address(request: HttpRequest) -> str:
        """
        Fetches user ip address from request.
        """
        return throttling.BaseThrottle().get_ident(request)

    def get_blacklisted_ips_from_db(self) -> Tuple[set, datetime.timedelta]:
        """
        Fetches blacklisted ips from database. Returns set of blacklisted ips and minimal
        time left to ip being liberated from blacklist. This time should be used as cache ttl
        lately.
        """
        blacklist_entries = self.model.objects.only_active().values(
            'ip',
            ttl=ExpressionWrapper(
                (F('record_time') + F('stretch')), output_field=DateTimeField()) - Now(),
        )
        return_ips_set = {entry['ip'] for entry in blacklist_entries}
        min_ttl = min(blacklist_entries, key=operator.itemgetter('ttl'))['ttl'] 

        return return_ips_set, min_ttl



    def is_ip_blacklisted(self, ip):
        """
        проверка айпи на вхождение в диапазон.
        :param ip:
        :return:
        """
        blacklisted_ips = self.cache.get_or_set(
            key=self.cache_key,
            timeout=self.cache_ttl,
            default=''
        )
