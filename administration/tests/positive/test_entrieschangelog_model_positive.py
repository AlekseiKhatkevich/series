from rest_framework.test import APITestCase
from django.forms.models import model_to_dict
import administration.models
from archives.tests.data import initial_data
from users.helpers import create_test_users
from rest_framework.reverse import reverse


class EntriesChangeLogModelPositiveTest(APITestCase):
    """
    Positive tests on 'EntriesChangeLog' model.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, *rest = cls.series

        cls.data = dict(
            content_object=cls.series_1,
            user=cls.user_1,
            as_who=administration.models.UserStatusChoices.CREATOR,
            operation_type=administration.models.OperationTypeChoices.CREATE,
            state=model_to_dict(cls.series_1),
        )

    def test_create_model_instance(self):
        """
        Check that if correct data is provided, than 'EntriesChangeLog' model instance
        can be successfully saved.
        """

        administration.models.EntriesChangeLog.objects.create(**self.data)

        self.assertEqual(
            1,
            administration.models.EntriesChangeLog.objects.count()
        )

    def test_str(self):
        """
        Check string representation of model instance
        """
        instance = administration.models.EntriesChangeLog.objects.create(**self.data)
        expected_str = f'pk = {instance.pk}, object = {instance.object_id},' \
                       f' operation_type = {instance.operation_type}'

        self.assertEqual(
            instance.__str__(),
            expected_str,
        )

    def test_get_absolute_url(self):
        """
        Check that 'get_absolute_url' returns correct url.
        """
        test_instance = administration.models.EntriesChangeLog.objects.create(**self.data)

        expected_url = reverse(
            'history-detail',
            args=[
                test_instance.content_object.__class__._meta.model_name,
                test_instance.object_id,
                test_instance.pk,
            ])

        self.assertEqual(
            test_instance.get_absolute_url,
            expected_url,
        )

