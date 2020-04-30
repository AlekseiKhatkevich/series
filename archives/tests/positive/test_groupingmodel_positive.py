from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model


class GroupingModelPositiveTest(APITestCase):
    """
    Tests for GroupingModel.
    """

    #fixtures = ('users.json',)

    def test__str__(self):
        """
        Test whether or not string representation works fine.
        """
        self.assertEqual(
            get_user_model().objects.all().count(),
            6
        )