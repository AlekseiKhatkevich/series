import more_itertools
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import error_codes
from series.helpers.test_helpers import TestHelpers
from users.helpers import create_test_users


class TvSeriesDetailUpdateDeleteNegativeTest(TestHelpers, APITestCase):
    """
    Negative test on detail/ update/ delete action on TvSeries model instances via API endpoint:
    /archives/tvseries/<series_pk>/ GET, PUT, PATCH.
    """

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

        self.seasons = initial_data.create_seasons(self.series)

    def test_forbid_access(self):
        """
        Check that only authenticated users are able to get read access to api endpoint.
        """
        response = self.client.get(
            reverse('tvseries-detail', args=(self.series_1.pk,)),
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=error_codes.DEFAULT_403_DRF_ERROR.message,
        )

    def test_if_allowed_redactors_hidden_for_random_user(self):
        """
        Check that if request user has no relations with object owner nor admin, then field
        'allowed_redactors' would be hidden for him.
        """
        series = self.series_1
        random_user = more_itertools.first_true(
            self.users,
            pred=lambda user: user != series.entry_author and not user.is_staff,
        )

        self.client.force_authenticate(user=random_user)

        response = self.client.get(
            reverse('tvseries-detail', args=(series.pk,)),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertNotIn(
            'allowed_redactors',
            response.data,
        )
