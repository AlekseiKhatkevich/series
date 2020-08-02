from rest_framework.test import APISimpleTestCase

import administration.serielizers


class HistoryAPIDetailNegativeTest(APISimpleTestCase):
    """
    Negative tests on models change history api detail action
    administration/history/<model name>/<instance_pk>/<pk>/.
    """
    maxDiff = None

    def test_calculate_difference(self):
        """
        Check that 'calculate_difference' method in 'HistoryDetailSerializer' serializer raises
        exception in case 'prev_state' and 'next_state' both None.
        """
        expected_error_message = \
            'Need to have either "prev_state" or "next_state", not both simultaneously.'
        serializer = administration.serielizers.HistoryDetailSerializer()
        state = prev_state = next_state = {'test': 'test'}

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            serializer.calculate_difference(state, prev_state=prev_state, next_state=next_state)