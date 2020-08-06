from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from users.helpers import create_test_users


class UserResourcesPositiveTest(APITestCase):
    """
    Test on user resources endpoints.
    users/entries/
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.images = initial_data.create_images_instances(cls.series, num_img=2)

        cls.seasons, cls.seasons_dict = initial_data.create_seasons(
            cls.series,
            num_seasons=3,
            return_sorted=True,
        )
        cls.season_1_1, cls.season_1_2, cls.season_1_3, *series_2_seasons = cls.seasons

    def test_series(self):
        """
        Check that endpoint displays series that belong to request user.
        """
        series = self.series_1
        user = series.entry_author

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['series']},
            {series.pk, },
        )
        self.assertSetEqual(
            {data['name'] for data in response.data['series']},
            {series.name, },
        )

    def test_seasons(self):
        """
        Check that endpoint displays seasons that belong to request user.
        """
        series = self.series_1
        user = series.entry_author
        seasons = self.seasons_dict[series.pk]

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['seasons']},
            {season.pk for season in seasons},
        )
        self.assertSetEqual(
            {data['series_name'] for data in response.data['seasons']},
            {series.name, },
        )
        self.assertSetEqual(
            {data['season_number'] for data in response.data['seasons']},
            {season.season_number for season in seasons},
        )

    def test_images(self):
        """
        Check that endpoint displays images that belong to request user.
        """
        series = self.series_1
        user = series.entry_author
        images = filter(lambda image: image.entry_author == user, self.images)

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('user-entries'),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertSetEqual(
            {data['pk'] for data in response.data['images']},
            {image.pk for image in images},
        )
        self.assertSetEqual(
            {data['model'] for data in response.data['images']},
            {series.__class__._meta.model_name, },
        )
        self.assertSetEqual(
            {data['object_name'] for data in response.data['images']},
            {series.name, },
        )


