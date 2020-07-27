import inspect
from administration.models import OperationTypeChoices, UserStatusChoices
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender='archives.SeasonModel')
@receiver(post_save, sender='archives.TvSeriesModel')
def create_log(sender, instance, **kwargs):
    """
    Create 'EntriesChangeLog' entries when seasons and series are saved.
    https://stackoverflow.com/questions/4721771/get-current-user-log-in-signal-in-django/8874383
    """
    #  If model instance is created by loading fixtures.
    if kwargs['raw']:
        return None

    for frame_record in inspect.stack():
        if frame_record[3] == 'get_response':
            request = frame_record[0].f_locals['request']
            break
    else:
        return None

    operation_status_options = OperationTypeChoices.CREATE.value if kwargs['created'] \
        else OperationTypeChoices.UPDATE

    instance.access_logs.create(
        user=request.user,
        as_who=getattr(instance, 'accessed_as_who', UserStatusChoices.CREATOR),
        operation_type=operation_status_options,
    )




