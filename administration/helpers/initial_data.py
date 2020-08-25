import random
from typing import Collection, Container, List, Union

import pytz
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from django.db.models.base import ModelBase
from django.forms.models import model_to_dict
from django.utils import timezone

from administration.models import EntriesChangeLog, IpBlacklist, OperationTypeChoices, UserStatusChoices
from series.helpers.context_managers import OverrideModelAttributes
from users.helpers.create_test_ips import generate_random_ip4

tz = pytz.timezone(settings.TIME_ZONE)


def generate_blacklist_ips(num_entries: int, num_active: int) -> List[IpBlacklist]:
    """
    Data generator for 'IpBlacklist' model for testing purposes.
    num_entries - number of entries to create.
    num_active - number of active entries among all entries.
    """
    assert num_entries >= num_active, 'Amount of entries should be gte than amount of active entries.'

    def generate_entry(active: bool = True) -> IpBlacklist:
        """
        Generate one 'IpBlacklist' entry.
        """
        entry = IpBlacklist(
            ip=generate_random_ip4(),
            stretch=timezone.timedelta(days=random.randrange(1, 30)),
            record_time=timezone.now() if active else (timezone.now() - timezone.timedelta(days=50)),
        )
        return entry

    active_entries = [generate_entry() for _ in range(num_active)]
    passive_entries = [generate_entry(active=False) for _ in range(num_entries - num_active)]

    with OverrideModelAttributes(model=IpBlacklist, field='record_time', auto_now_add=False):
        resulted_entries = IpBlacklist.objects.bulk_create(active_entries + passive_entries)

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

