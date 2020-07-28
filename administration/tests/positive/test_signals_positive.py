from collections import namedtuple

from rest_framework.test import APITestCase

import administration.models
import archives.models
from administration.signals import create_log
from archives.tests.data import initial_data
from users.helpers import create_test_users


class SignalsPositiveTest(APITestCase):
    """
    Positive test on signals in 'administration' app.
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

    def test_create_log_sender_instance_created_and_updated(self):
        """
        Check that in create_log 'EntriesChangeLog' is created on sender's model instance creation or update.
        """
        self.request.user = self.series_1.entry_author

        kwargs_created = {'raw': False, 'created': True, }
        kwargs_updated = {'raw': False, 'created': False, }

        for kwargs in (kwargs_created, kwargs_updated):
            with self.subTest(kwargs=kwargs):

                create_log(
                        sender=archives.models.TvSeriesModel,
                        instance=self.series_1,
                        request=self.request,
                        **kwargs,
                    )
                operation_type = administration.models.OperationTypeChoices.CREATE if kwargs['created'] \
                    else administration.models.OperationTypeChoices.UPDATE

                self.assertTrue(
                    administration.models.EntriesChangeLog.objects.filter(
                        object_id=self.series_1.pk,
                        user=self.series_1.entry_author,
                        as_who=administration.models.UserStatusChoices.CREATOR,
                        operation_type=operation_type,
                        content_type__model=archives.models.TvSeriesModel.__name__.lower(),
                        content_type__app_label=archives.models.TvSeriesModel._meta.app_label.lower(),
                    ).exists()
                )
