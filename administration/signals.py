import inspect
from typing import Optional

from django.core.cache import cache
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.http import HttpRequest
from django.utils import timezone

from administration.models import OperationTypeChoices, UserStatusChoices
from series import constants


@receiver([post_save, post_delete, ], sender='django_db_logger.StatusLog')
def change_api_updated_at(sender: ModelBase, instance: ModelBase, **kwargs) -> None:
    """
    Signal handler sets time of delete or create operation in cache.
    """
    default_timeout = 60 * 60
    model_name = sender._meta.model_name
    cache.set(
        key='api_updated_at_timestamp',
        value=timezone.now().isoformat(),
        timeout=constants.TIMEOUTS.get(model_name, default_timeout),
        version=model_name,
    )


@receiver([post_save, post_delete, ], sender='archives.ImageModel')
@receiver([post_save, post_delete, ], sender='archives.SeasonModel')
@receiver([post_save, post_delete, ], sender='archives.TvSeriesModel')
def create_log(sender: ModelBase,
               instance: ModelBase,
               request: Optional[HttpRequest] = None,
               **kwargs,
               ) -> None:
    """
    Create 'EntriesChangeLog' entries when seasons, images and series are saved and deleted.
    https://stackoverflow.com/questions/4721771/get-current-user-log-in-signal-in-django/8874383
    """
    #  If model instance is created by loading fixtures. 'raw' isn't present in *_delete signals.
    if kwargs.get('raw', None):
        return None

    #  Get 'request' objects from stack trace if possible. Found on iteration 49 from 62, so that
    #  should be faster with reversed().
    if request is None:
        for frame_record in reversed(inspect.stack()):
            if frame_record.function == 'get_response':
                request = frame_record.frame.f_locals['request']
                break
        else:
            return None

    # 'created' isn't present in *_delete signals.
    try:
        if kwargs['created']:
            operation_type = OperationTypeChoices.CREATE
        else:
            operation_type = OperationTypeChoices.UPDATE
    except KeyError:
        operation_type = OperationTypeChoices.DELETE

    # 'accessed_as_who' attribute is assigned in permissions.
    instance.access_logs.create(
        user=request.user,
        as_who=getattr(instance, 'accessed_as_who', UserStatusChoices.CREATOR),
        operation_type=operation_type,
        state=model_to_dict(instance),
    )
