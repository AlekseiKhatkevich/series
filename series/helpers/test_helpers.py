import functools
from typing import Callable, Optional

from django.conf import settings as django_settings
from django.core.cache import cache, caches
from rest_framework import exceptions, settings as drf_settings, status, test, throttling
from rest_framework.response import Response
from rest_framework.reverse import reverse


def switch_off_validator(validator_name: str) -> Callable:
    """
    Switches of chosen validator temporarily in tests.
    Validator should implement extra functionality ti do so.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = django_settings.VALIDATOR_SWITCH_OFF_KEY
            try:
                cache.set(key, True, 1, version=validator_name)
                value = func(*args, **kwargs)
            finally:
                cache.delete(key, version=validator_name)
            return value
        return wrapper
    return decorator


class TestHelpers(test.APISimpleTestCase):
    """
    Collection of helper methods for tests.
    """

    def check_status_and_error_message(
            self,
            response: Response,
            /,
            *,
            field: Optional[str] = 'detail',
            error_message: str,
            status_code: str
    ) -> None:
        """
        Helper function to check response status code and exception message in one go.
        :param response: DRF response.
        :param field: field of expected exception.
        :param error_message: Expected error message.
        :param status_code: Expected status code.
        :return: None
        """
        value = response.data[field]if field is not None else response.data[0]

        if isinstance(value, exceptions.ErrorDetail):
            error_in_response = str(value)
        elif isinstance(value, str):
            error_in_response = value
        else:
            error_in_response = value[0]

        self.assertEqual(
            response.status_code,
            status_code,
        )
        self.assertEquals(
            error_in_response,
            error_message
        )

    def check_scope_throttling(
            self,
            *,
            scope: str,
            url_name: str,
            data: dict,
            http_verb: str,
            **kwargs) -> None:
        """
         Check whether scope throttling is applied.
        :param scope: Throttling scope.
        :param url_name: Base url name for 'reverse' function.
        :param data: Request data.
        :param http_verb: Http verb for this API action.
        :param kwargs: Extra request header strings.
        :return: None
        """
        cache_name = django_settings.SCOPE_THROTTLING_CACHE
        throttler = throttling.ScopedRateThrottle()
        rate = drf_settings.api_settings.DEFAULT_THROTTLE_RATES[scope]
        overflow_rate = throttler.parse_rate(rate)[0] + 1

        client = getattr(self.client, http_verb.lower())

        for _ in range(overflow_rate):
            response = client(
                reverse(url_name),
                data=data,
                format='json',
                **kwargs
            )
        self.assertEqual(
            response.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS
        )

        caches[cache_name].clear()

