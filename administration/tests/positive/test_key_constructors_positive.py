from django.core.cache import cache
from django.utils import timezone
from django_db_logger.models import StatusLog
from rest_framework.test import APISimpleTestCase
from rest_framework.views import APIView

import administration.serielizers
from administration import key_constructors


class KeyConstructorsAndBitsPositiveTest(APISimpleTestCase):
    """
    Positive test on cache keys constructors and their bits in 'administration' app.
    """
    maxDiff = None

    def test_UpdatedAtKeyBit(self):
        """
        Check that 'UpdatedAtKeyBit' sets cache key if it is not present in cache yet or returns
        it's value otherwise.
        """
        view_instance = APIView()
        view_instance.model = StatusLog
        bit = key_constructors.UpdatedAtKeyBit()
        cache.delete(key=bit.cache_key, version=view_instance.model._meta.model_name)
        operation_date = bit.get_data(
            params={},
            view_instance=view_instance,
            view_method='get',
            request=None,
            args=(),
            kwargs={},
        )
        self.assertAlmostEqual(
            timezone.datetime.fromisoformat(operation_date),
            timezone.now(),
            delta=timezone.timedelta(seconds=1),
        )

        cache.set(key=bit.cache_key, version=view_instance.model._meta.model_name, value='test')
        value_from_cache = bit.get_data(
            params={},
            view_instance=view_instance,
            view_method='get',
            request=None,
            args=(),
            kwargs={},
        )
        self.assertEqual(
            value_from_cache,
            'test',
        )
        cache.delete(key=bit.cache_key, version=view_instance.model._meta.model_name)

    def test_HistoryViewSetLastOperationBit(self):
        """
        Check that 'HistoryViewSetLastOperationBit' bit gets last operation datetime in iso format
        from cache. If cache key is not present, it saves ast operation datetime  in cache then.
        """
        view_instance = APIView()
        view_instance.serializer_class = administration.serielizers.HistorySerializer
        view_instance.kwargs = dict()
        view_instance.kwargs['model_name'] = 'tvseriesmodel'
        view_instance.kwargs['instance_pk'] = 1
        bit = key_constructors.HistoryViewSetLastOperationBit()

        cache.delete(key=bit.cache_key, version=('tvseriesmodel', 1))

        operation_date = bit.get_data(
            params={},
            view_instance=view_instance,
            view_method='get',
            request=None,
            args=(),
            kwargs={},
        )

        self.assertAlmostEqual(
            timezone.datetime.fromisoformat(operation_date),
            timezone.now(),
            delta=timezone.timedelta(seconds=1),
        )

        cache.set(key=bit.cache_key, version=('tvseriesmodel', 1), value='test')
        value_from_cache = bit.get_data(
            params={},
            view_instance=view_instance,
            view_method='get',
            request=None,
            args=(),
            kwargs={},
        )
        self.assertEqual(
            value_from_cache,
            'test',
        )
        cache.delete(key=bit.cache_key, version=('tvseriesmodel', 1))



