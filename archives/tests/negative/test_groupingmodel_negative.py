from django.core import exceptions
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
import archives.models
from series import error_codes
from users.helpers import create_test_users


class GroupingModelNegativeTest(APITestCase):
    """
    Tests for GroupingModel.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.series_1, cls.series_2, *tail = initial_data.create_tvseries(users=cls.users)

    def test_interrelationship_on_self_constraint(self):
        """
        Check that if model instance has interrelationship on itself, that is
        'from_series' == 'to_series', then IntegrityError would be arisen.
        """
        expected_error_message = 'interrelationship_on_self'

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            self.series_1.interrelationship.add(self.series_1)

    def test_clean_to_series_equal_from_series(self):
        """
        Check that if 'Tvseries' model entry points to self, then validation error would be arisen
        by 'clean()' method in intermediate model 'GroupingModel'.
        """
        expected_error_message = error_codes.INTERRELATIONSHIP_ON_SELF.message

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            archives.models.GroupingModel.objects.create(
                from_series=self.series_1,
                to_series=self.series_1,
                reason_for_interrelationship='test',
             )

