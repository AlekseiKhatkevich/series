import random
from typing import Collection, Container, Iterable, List, Union

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.db.models.base import ModelBase
from django.forms.models import model_to_dict
from django.utils import timezone

from administration.models import EntriesChangeLog, IpBlacklist, OperationTypeChoices, \
    UserStatusChoices
from series.helpers.context_managers import OverrideModelAttributes
from users.helpers.create_test_ips import generate_random_ip4, generate_random_ip6, \
    generate_random_ip_network

tz = pytz.timezone(settings.TIME_ZONE)


def generate_blacklist_ips(num_entries: int,
                           num_active: int,
                           protocols: Iterable = (4, ),
                           num_networks: int = 0,
                           ) -> List[IpBlacklist]:
    """
    Data generator for 'IpBlacklist' model for testing purposes.
    num_entries - number of entries to create.
    num_active - number of active entries among all entries.
    protocol == 4 - generate ipv4 ip addresses.
    protocol == 6 - generate ipv6 ip addresses.
    num_networks - generate X pcs. networks according specified protocol.
    """
    assert num_entries >= num_active, 'Amount of entries should be gte than amount of active entries.'
    assert protocols, 'Specify at least one address protocol.'
    assert num_networks >= 0, 'Specify positive integer for number of networks to create.'

    def generate_entry(protocol: int, active: bool = True, network: bool = False) -> IpBlacklist:
        """
        Generate one 'IpBlacklist' entry.
        """
        assert protocol in (4, 6, ), 'Choose protocol version 4 or 6.'

        if not network:
            ip = generate_random_ip4() if protocol == 4 else generate_random_ip6()
        else:
            ip = generate_random_ip_network(protocol=protocol, max_bit_down=8)

        entry = IpBlacklist(
            ip=ip,
            stretch=timezone.timedelta(days=random.randrange(1, 30)),
            record_time=timezone.now() if active else (timezone.now() - timezone.timedelta(days=50)),
        )

        return entry

    entries_pool = []
    for version in protocols:
        active_entries = [
            generate_entry(version) for _ in range(num_active)
        ]
        passive_entries = [
            generate_entry(version, active=False) for _ in range(num_entries - num_active)
        ]
        networks = [
            generate_entry(version, network=True) for _ in range(num_networks)
        ]
        entries_pool.extend(
            active_entries + passive_entries + networks
        )

    with OverrideModelAttributes(model=IpBlacklist, field='record_time', auto_now_add=False):
        resulted_entries = IpBlacklist.objects.bulk_create(entries_pool)

    return resulted_entries


def generate_changelog(
        instance: ModelBase,
        user: Union[get_user_model(), Container[get_user_model()], QuerySet],
        num_logs: int = 10,
) -> List[EntriesChangeLog]:
    """
    Generates 'EntriesChangeLog' entries for given instance.
    """
    count = 1

    def generate_one_entry() -> EntriesChangeLog:
        """
        Generates one 'EntriesChangeLog' instance.
        """
        nonlocal count

        if count == 1:
            operation_type = OperationTypeChoices.CREATE
        elif count == num_logs:
            operation_type = OperationTypeChoices.DELETE
        else:
            operation_type = OperationTypeChoices.UPDATE

        one_entry = EntriesChangeLog(
            content_object=instance,
            user=random.choice(user) if isinstance(user, (Collection, QuerySet)) else user,
            as_who=random.choice(UserStatusChoices.values),
            operation_type=operation_type,
            state=model_to_dict(instance),
            access_time=tz.normalize(timezone.now() + timezone.timedelta(hours=count))
        )

        count += 1

        return one_entry

    with OverrideModelAttributes(model=EntriesChangeLog, field='access_time', auto_now_add=False):
        log_entries = EntriesChangeLog.objects.bulk_create(
            [generate_one_entry() for _ in range(num_logs)]
        )

    return log_entries
