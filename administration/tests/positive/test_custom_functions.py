from django.db.models import Count, Min
from django_db_logger.models import StatusLog
from rest_framework.test import APITestCase

import administration.models
from administration.helpers.initial_data import generate_blacklist_ips
from administration.tasks import clear_old_logs, delete_non_active_blacklisted_ips


class DeleteOldLogsPositiveTest(APITestCase):
    """
    Positive tests on function that deletes old logs.
    """
    maxDiff = None
    fixtures = ('logs_dump.json',)

    def test_delete_old_logs(self):
        """
        Check that 'delete_old_logs' actually deletes old logs.
        """
        aggregation = StatusLog.objects.aggregate(oldest=Min('create_datetime'), count=Count('*'))
        oldest_entry, count = aggregation['oldest'], aggregation['count']

        clear_old_logs(count // 2)

        self.assertFalse(
            StatusLog.objects.filter(create_datetime=oldest_entry).exists()
        )
        self.assertEqual(
            StatusLog.objects.all().count(),
            count // 2,
        )

    def test_delete_non_active_blacklisted_ips_celery_task(self):
        """
        Check that 'delete_non_active_blacklisted_ips' deletes non-active 'IpBlacklist' entries.
        """
        generate_blacklist_ips(10, 7, )

        with self.assertNumQueries(2):
            delete_non_active_blacklisted_ips()

        self.assertEqual(
            administration.models.IpBlacklist.objects.all().count(),
            7,
        )

