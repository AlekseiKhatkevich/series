import datetime
import importlib.util
import unittest

from rest_framework.test import APITestCase

import administration.cache_functions


@unittest.skipUnless(importlib.util.find_spec('coverage'), '"coverage" module is not installed.',)
class CacheFunctionsPositiveTest(APITestCase):
    """
    Positive test on auxiliary functions used to calculate, invalidate, etc cache and cache
    keys in 'administration' app.
    """
    maxDiff = None

    def test_get_coverage_last_time(self):
        """
        Check that 'get_coverage_last_tim' function would return datetime of last coverage
        calculation being made over tests.
        """
        result = administration.cache_functions.get_coverage_last_time()

        self.assertIsInstance(
            result,
            datetime.datetime,
        )
