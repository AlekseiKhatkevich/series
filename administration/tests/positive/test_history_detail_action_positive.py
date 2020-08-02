from rest_framework import status
from rest_framework.test import APITestCase

from administration.helpers.initial_data import generate_changelog
from archives.tests.data import initial_data
from users.helpers import create_test_users


class HistoryAPIDetailPositiveTest(APITestCase):
    """
    Positive tests on models change history api detail action
    administration/history/<model name>/<instance_pk>/<pk>/.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.logs = generate_changelog(self.series_1, self.user_1)

    def test_retrieve_action(self):
        """
        Check that GET request on retrieve action api returns full information about individual
        history log.
        """
        test_log = self.logs[len(self.logs) // 2]
        prev_log = test_log.get_previous_by_access_time()
        next_log = test_log.get_next_by_access_time()

        prev_log.state['name'] = 'prev_state'
        prev_log.save()

        next_log.state['name'] = 'next_state'
        next_log.save()

        self.client.force_authenticate(user=self.series_1.entry_author)

        response = self.client.get(
            test_log.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        for state in ('state', 'prev_state', 'next_state',):
            with self.subTest(state=state):
                self.assertIn(
                    state,
                    response.data
                )
                self.assertIsNotNone(
                    state
                )

        for state in ('prev_state', 'next_state',):
            with self.subTest(state=state):
                self.assertEqual(
                    response.data[state]['name'],
                    state
                )

        for change in ('prev_changes', 'next_changes'):
            with self.subTest(state=state):
                self.assertIn(
                    change,
                    response.data
                )
                self.assertEqual(
                    response.data[change],
                    {'name', }
                )

    def test_retrieve_action_no_previous_or_next_state(self):
        """
        Check that 'prev_changes' or 'next_changes' would return Null if there are no previous or
        next states exist.
        """
        test_log_prev = self.logs[0]
        test_log_next = self.logs[-1]

        self.client.force_authenticate(user=self.series_1.entry_author)

        for field, log in zip(('prev_changes', 'next_changes'), (test_log_prev, test_log_next)):
            with self.subTest(field=field, log=log):
                response = self.client.get(
                    log.get_absolute_url,
                    data=None,
                    format='json',
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )
                self.assertIsNone(
                    response.data[field]
                )

    def test_no_changes_detected(self):
        """
        check that if no changes detected, than 'prev_changes' or 'next_changes'
        would return None.
        """
        test_log = self.logs[len(self.logs) // 2]

        self.client.force_authenticate(user=self.series_1.entry_author)

        response = self.client.get(
            test_log.get_absolute_url,
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIsNone(
            response.data['prev_changes']
        )
        self.assertIsNone(
            response.data['next_changes']
        )
