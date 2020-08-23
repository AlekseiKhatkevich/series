import inspect
from typing import Optional

from django.conf import settings
from django.core.cache import cache, caches
from django.db.models.base import ModelBase
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.forms.models import model_to_dict
from django.http import HttpRequest
from django.utils import timezone

from administration.models import EntriesChangeLog, OperationTypeChoices, UserStatusChoices
from series import constants

default_timeout = constants.TIMEOUTS['default']


@receiver([post_save, post_delete, ], sender='administration.IpBlacklist')
def invalidate_blacklist_cache(*args, **kwargs) -> None:
    """
    Invalidates blacklist cache by deleting it's key from cache.
    """
    blacklist_cache = caches[settings.BLACKLIST_CACHE]
    blacklist_cache_key = constants.IP_BLACKLIST_CACHE_KEY

    blacklist_cache.delete(blacklist_cache_key)


@receiver([post_save, post_delete, ], sender='django_db_logger.StatusLog')
def change_api_updated_at(sender: ModelBase, instance: ModelBase, **kwargs) -> None:
    """
    Signal handler sets time of delete or create operation in cache.
    """
    model_name = sender._meta.model_name
    cache.set(
        key='api_updated_at_timestamp',
        value=timezone.now().isoformat(),
        timeout=constants.TIMEOUTS.get(model_name, default_timeout),
        version=model_name,
    )


@receiver([post_save, post_delete, ], sender=EntriesChangeLog)
def last_operation_time_entrieschangelog(sender: ModelBase, instance: EntriesChangeLog, **kwargs) -> None:
    """
    Sets in cache last operation datetime for 'EntriesChangeLog' model in 'administration' app.
    """
    sender_model_name = sender._meta.model_name
    contenttype_model_name = instance.content_type.model
    version = (contenttype_model_name, instance.object_id)
    cache.set(
        key='last_operation_time_entrieschangelog',
        value=timezone.now().isoformat(),
        timeout=constants.TIMEOUTS.get(sender_model_name, default_timeout),
        version=version,
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
