from django.db.models import Count, Min
from django_db_logger.models import StatusLog
from rest_framework.test import APITestCase

from administration.tasks import clear_old_logs


class DeleteOldLogsPositiveTest(APITestCase):
    """
    Positive tests on function that deletes old logs.
    """
    maxDiff = None
    fixtures = ('logs_dump.json', )

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




# class CustomFunctionsPositiveTest(IsolatedAsyncioTestCase):
#     """
#     Positive test on 'Administration' app custom functions.
#     """
#     maxDiff = None
#
#     def asyncSetUp(self) -> None:
#         self.users = create_test_users.create_users()
#         self.user_1, self.user_2, self.user_3 = self.users
#
#         self.series = initial_data.create_tvseries(self.users)
#         self.series_1, self.series_2 = self.series
#
#     @unittest.skip
#     async def test_HandleWrongUrls(self):
#         """
#         Check that 'HandleWrongUrls' class instance being called sends email to users who is
#         in charge for series where invalid urls are found.
#         """
#         fake_url = 'https://www.imdb.com/fake'
#         self.series_1.imdb_url = fake_url
#         self.series_1.save()
#
#         expected_result = f'There are {1} series with invalid urls.'
#
#         result = administration.handle_urls.HandleWrongUrls()()
#
#         self.assertEqual(
#             expected_result,
#             result,
#         )


