import more_itertools
from rest_framework import status
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
    maxDiff = None

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
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )
        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=error_codes.DRF_NO_AUTH.message,
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
            self.series_1.get_absolute_url,
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

    def test_if_allowed_redactors_hidden_during_update(self):
        """
        Check that 'allowed_redactors' would not be present in response data after update /
        partial update operations.
        """
        user = self.series_1.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.patch(
            self.series_1.get_absolute_url,
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

    def test_random_user_can_not_update_series(self):
        """
        Check that user who is not an author, master, slave of author'sfirnd  - does not have
        an access to update series api endpoint.
        """

        random_user = more_itertools.first_true(
            self.users,
            pred=lambda user: user != self.series_1.entry_author and not user.is_staff,
        )

        self.client.force_authenticate(user=random_user)

        response = self.client.patch(
            self.series_1.get_absolute_url,
            data=None,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=error_codes.DRF_NO_PERMISSIONS.message,
        )
