from rest_framework.response import Response
from rest_framework.test import APISimpleTestCase


class TestHelpers(APISimpleTestCase):
    """
    Collection of helper methods for tests.
    """
    def check_status_and_error(
            self, response: Response, *, field: str, error_message: str, status_code: str
    ) -> None:
        """
        Helper function to check response status code and exception message in one go.
        :param response: DRF response.
        :param field: field of expected exception.
        :param error_message: Expected error message.
        :param status_code: Expected status code.
        :return: None
        """
        if isinstance(response.data[field], str):
            error_in_response = response.data[field]
        else:
            error_in_response = response.data[field][0]

        self.assertEqual(
            response.status_code,
            status_code,
        )
        self.assertEquals(
            error_in_response,
            error_message
        )