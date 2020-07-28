from django.core import exceptions
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

import administration.models
from archives.tests.data import initial_data
from users.helpers import create_test_users


class EntriesChangeLogModelNegativeTest(APITestCase):
    """
    Negative tests on 'EntriesChangeLog' model.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, *rest = cls.series

    def setUp(self) -> None:
        self.data = dict(
            content_object=self.series_1,
            user=self.user_1,
            as_who=administration.models.UserStatusChoices.CREATOR,
            operation_type=administration.models.OperationTypeChoices.CREATE,
        )

    def test_as_who_check_constraint(self):
        """
        Check that 'as_who_check' doesn't allow to save data with 'as_who' outside defined choices.
        """
        expected_error_message = 'as_who_check'
        self.data['as_who'] = 'test'

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            instance = administration.models.EntriesChangeLog(**self.data)
            instance.save(fc=False)

    def test_operation_type_check_constraint(self):
        """
        Check that 'operation_type_check' doesn't allow to save data with 'operation_type' outside
         defined choices.
        """
        expected_error_message = 'operation_type_check'
        self.data['operation_type'] = 'test'

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            instance = administration.models.EntriesChangeLog(**self.data)
            instance.save(fc=False)

    def test_full_clean(self):
        """
        Check that 'full_clean' method gets involved on model save.
        """
        self.data['operation_type'] = 'test'

        with self.assertRaises(exceptions.ValidationError):
            instance = administration.models.EntriesChangeLog(**self.data)
            instance.save(fc=True)

