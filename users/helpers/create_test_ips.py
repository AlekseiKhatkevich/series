import ipaddress
import random
from datetime import datetime, timedelta
from typing import Sequence

import pytz
from django.conf import settings
from django.utils import timezone

import users.models as users_models
from series.helpers import context_managers
from series.helpers.typing import User_instance, ip_instance

tz = pytz.timezone(settings.TIME_ZONE)


def generate_random_ip4() -> str:
    """
    Generates random ip4 address.
    """
    return ipaddress.IPv4Address(random.randint(0, 2 ** 32 - 1)).compressed


def generate_random_ip6() -> str:
    """
    Generates random ip6 address.
    """
    return ipaddress.IPv6Address(random.randint(0, 2 ** 128 - 1)).compressed


def generate_random_ip_network(protocol: int, max_bit_down: int) -> str:
    """
    Generates random ipv4 or ipv6 networks.
    """
    assert protocol in (4, 6, ), 'Choose protocol version 4 or 6.'

    if protocol == 4:
        return ipaddress.IPv4Network(
            random.randint(0, 2 ** 32 - 1)
        ).supernet(
            prefixlen_diff=random.randint(1, max_bit_down)
        ).compressed
    else:
        return ipaddress.IPv6Network(
            random.randint(0, 2 ** 128 - 1)
        ).supernet(
            prefixlen_diff=random.randint(1, max_bit_down)
        ).compressed


def offset_time(time: datetime, max_offset: int, min_offset: int = 0) -> datetime:
    """
    Changes time a little bit randomly backwards in past.
    max_offset, min_offset - seconds, integers.
    """
    random_offset = random.randrange(max_offset - min_offset)
    time_with_offset = tz.normalize(time - timedelta(seconds=random_offset))
    return time_with_offset


def create_ip_entries(users: Sequence[User_instance]) -> Sequence[ip_instance]:
    """
    Creates 'UserIP' entries for tests.
    """
    ips_list = [users_models.UserIP(
            user=user,
            ip=generate_random_ip4(),
            sample_time=offset_time(timezone.now(), 86400, 3600),
        ) for _ in range(3) for user in users
    ]

    with context_managers.OverrideModelAttributes(
            model=users_models.UserIP,
            field='sample_time',
            auto_now=False
    ):
        ips = users_models.UserIP.objects.bulk_create(ips_list)

    return ips
