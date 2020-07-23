from django.conf import settings
from django.core import mail
from rest_framework.test import APITestCase

import administration.tasks
import archives.models
from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class SendEmailsPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on sending notification emails to responsible users in case their series
    entries have invalid urls.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def tearDown(self) -> None:
        mail.outbox = []

    def test_send_one_email_function(self):
        """
        Check that 'send_one_email' sends email to a list os recipients.
        """
        series = archives.models.TvSeriesModel.objects.annotate_with_responsible_user().\
            values('name', 'imdb_url', 'responsible', ).first()

        administration.tasks.send_one_email(series=series)

        self.assertEqual(
            len(mail.outbox),
            1,
        )
        self.assertIn(
            series['responsible'],
            mail.outbox[0].to,
        )
        self.assertIn(
            series['name'],
            mail.outbox[0].subject,
        )
        self.assertIn(
            series['imdb_url'],
            mail.outbox[0].body,
        )

    def test_test_send_one_email_no_responsible_user(self):
        """
        Check that 'send_one_email' sends email to admin in case there are no any responsible
        users alive.
        """
        author = self.series_1.entry_author
        author.delete()

        admin_email = settings.ADMINS[0][-1]

        series = archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk).\
            annotate_with_responsible_user().values('name', 'imdb_url', 'responsible', ).first()

        administration.tasks.send_one_email(series=series)

        self.assertIn(
            admin_email,
            mail.outbox[0].to,
        )