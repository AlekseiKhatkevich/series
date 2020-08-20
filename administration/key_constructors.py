from django.core.cache import cache
from django.utils import timezone
from rest_framework_extensions.key_constructor import bits
from rest_framework_extensions.key_constructor.constructors import KeyConstructor

from series import constants


class UpdatedAtKeyBit(bits.KeyBitBase):
    """
    Returns current datetime str representation. Sets it in cache if one is not present yet.
    """
    cache_key = 'api_updated_at_timestamp'

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        version = view_instance.model._meta.model_name

        value = cache.get_or_set(
            key=self.cache_key,
            default=timezone.now().isoformat(),
            timeout=constants.TIMEOUTS[version],
            version=version,
        )
        return value


class LastChangeTimeBit(bits.ListModelKeyBit):
    """
    Returns last 'create_datetime' datetime casted in iso format.
    """

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        [last_create_time] = view_instance.get_queryset().order_by('-create_datetime')[:1].\
            values_list('create_datetime', flat=True)

        return last_create_time.isoformat()


class LogsListViewKeyConstructor(KeyConstructor):
    """
    Key constructor for 'LogsListView'.
    """
    unique_method_id = bits.UniqueMethodIdKeyBit()
    query_param = bits.QueryParamsKeyBit()
    last_change_time = UpdatedAtKeyBit()


class HistoryViewSetLastOperationBit(bits.KeyBitBase):
    """
    Fetches last operation time in model 'EntriesChangeLog' grouped by 'object_id' from cache. If not
    present in cache - adds it in cache.
    """
    cache_key = 'last_operation_time_entrieschangelog'

    def get_data(self, params, view_instance, view_method, request, args, kwargs):
        model_name = view_instance.serializer_class.Meta.model._meta.model_name
        archives_model_name = view_instance.kwargs['model_name']
        archives_instance_pk = view_instance.kwargs['instance_pk']
        version = (archives_model_name, archives_instance_pk)

        value = cache.get_or_set(
            key=self.cache_key,
            default=timezone.now().isoformat(),
            timeout=constants.TIMEOUTS[model_name],
            version=version,
        )
        return value


class HistoryViewSetListActionKeyConstructor(KeyConstructor):
    """
    Cache key constructor for 'HistoryViewSet' list action.
    """
    unique_method_id = bits.UniqueMethodIdKeyBit()
    query_param = bits.QueryParamsKeyBit()
    last_operation_time = HistoryViewSetLastOperationBit()
