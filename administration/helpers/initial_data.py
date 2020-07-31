import random
from typing import Collection, Container, List, Union

from django.contrib.auth import get_user_model
from django.db.models.base import ModelBase
from django.db.models import QuerySet
from django.forms.models import model_to_dict

from administration.models import EntriesChangeLog, OperationTypeChoices, UserStatusChoices


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
        )

        count += 1

        return one_entry

    log_entries = EntriesChangeLog.objects.bulk_create(
        [generate_one_entry() for _ in range(num_logs)]
    )

    return log_entries
