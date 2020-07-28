from collections import namedtuple

from rest_framework.test import APITestCase

import administration.models
import archives.models
from administration.signals import create_log
from archives.tests.data import initial_data
from users.helpers import create_test_users


class SignalsNegativeTest(APITestCase):
    """
    Negative test on signals in 'administration' app.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.request = namedtuple('request', ['user', ])

    def test_create_log_fixtures(self):
        """
        Check that 'create_log' signal handler is invoked during model instances creation process
        in fixtures, than it would not create log instance at all.
        """
        self.request.user = self.series_1.entry_author
        kwargs = {'raw': True, 'created': True, }

        create_log(
            sender=archives.models.TvSeriesModel,
            instance=self.series_1,
            request=self.request,
            **kwargs,
        )

        self.assertFalse(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=self.series_1.pk,
                user=self.series_1.entry_author,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.CREATE,
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ).exists()
        )

    def test_create_log_no_request(self):
        """
        Check that 'create_log' signal handler is invoked during model instances creation process
       and we can not fetch request from stack, than it would not create log instance at all.
        """
        kwargs = {'raw': False, 'created': True, }

        create_log(
            sender=archives.models.TvSeriesModel,
            instance=self.series_1,
            **kwargs,
        )

        self.assertFalse(
            administration.models.EntriesChangeLog.objects.filter(
                object_id=self.series_1.pk,
                user=self.series_1.entry_author,
                as_who=administration.models.UserStatusChoices.CREATOR,
                operation_type=administration.models.OperationTypeChoices.CREATE,
                content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
            ).exists()
        )
