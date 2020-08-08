import itertools
import operator

from django.db.models import F, Window, functions
from rest_framework.test import APITestCase

import administration.models
import users.models
from administration.helpers.initial_data import generate_changelog
from archives.tests.data import initial_data
from users import database_functions
from users.helpers import create_test_ips, create_test_users


class CustomFunctionsIpCountPositiveTest(APITestCase):
    """
    Positive test on custom database function 'IpCount' in 'users' app.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.ips = create_test_ips.create_ip_entries(cls.users)
        key = operator.attrgetter('user_id')
        ips_grouped_by_user_id = itertools.groupby(sorted(cls.ips, key=key), key=key)
        # user to list of user's ips mapping
        cls.grouped_dict = {user_id: tuple(ips) for user_id, ips in ips_grouped_by_user_id}

    def test_IpCount_lte_limit(self):
        """
        Check that 'IpCount' would return True if objects count is less or equals then limit.
        """
        limit = 4
        test_user = self.user_3

        self.assertTrue(
            users.models.UserIP.objects.all().annotate(
                result=database_functions.IpCount(
                    test_user.pk,
                    limit)
            ).first().result
        )

    def test_IpCount_gt_limit(self):
        """
        Check that 'IpCount' would return True if objects count is less or equals then limit.
        """
        limit = 2
        test_user = self.user_3

        self.assertFalse(
            users.models.UserIP.objects.all().annotate(
                result=database_functions.IpCount(
                    test_user.pk,
                    limit)
            ).first().result
        )


class CustomFunctionsJSONDiffPositiveTest(APITestCase):
    """
    Positive test on custom database function 'JSONDiff' in 'users' app.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.logs = generate_changelog(cls.series_1, cls.user_1)

    def test_json_difference(self):
        """
        Check that 'JSONDiff' database function would return difference between 2 JSONs.
        """
        for log in self.logs:
            log.state['id'] = log.pk

        administration.models.EntriesChangeLog.objects.bulk_update(
            self.logs, ['state', ]
        )
        prev_val = Window(
            expression=functions.Lag('state'),
            partition_by=(F('content_type_id'), F('object_id'),),
            order_by=F('access_time').asc(),
        )
        qs = administration.models.EntriesChangeLog.objects.annotate(
            diff=users.database_functions.JSONDiff(prev_val,  F('state'))
            )
        for item in qs:
            with self.subTest(item=item):
                if item.diff is not None:
                    self.assertEqual(
                        item.diff['id'],
                        item.pk - 1,
                    )


