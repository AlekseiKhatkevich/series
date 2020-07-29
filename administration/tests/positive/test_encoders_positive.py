from rest_framework.test import APISimpleTestCase

from administration import encoders
from archives.helpers.custom_functions import daterange
import json


class EncodersPositiveTest(APISimpleTestCase):
    """
    Positive tests on 'administration' app encoders.
    """
    maxDiff = None

    def test_CustomEncoder(self):
        """
        Check that 'CustomEncoder' correctly encodes daterange instance.
        """
        expected_result = json.dumps({"lower": "2020-02-25", "upper": "2020-03-01", "bounds": "[)"})
        daterange_instance = daterange((2020, 2, 25), (2020, 3, 1))

        actual_result = encoders.CustomEncoder().encode(daterange_instance)

        self.assertJSONEqual(
            actual_result,
            expected_result,
        )
