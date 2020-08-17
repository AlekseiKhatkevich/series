from rest_framework_extensions.key_constructor.constructors import (
    KeyConstructor
)
from rest_framework_extensions.key_constructor import bits


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
    pagination = bits.PaginationKeyBit()
    last_change_time = LastChangeTimeBit()
