from django.conf import settings
from django.core import files
from rest_framework.test import APITestCase

from archives import models
from archives.tests.data import initial_data
from users.helpers import create_test_users


class CreateInitialDataPositiveTest(APITestCase):
    """
    Test process and result of creating test initial data for 'Archives' app tests.
    """

    original_media_root = settings.MEDIA_ROOT

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()

    def test_create_tvseries(self):
        """
        Check whether or not series are created after running a script.
        """

        series = initial_data.create_tvseries(users=self.users)

        self.assertEqual(
            models.TvSeriesModel.objects.all().count(),
            len(series)
        )

    def test_create_seasons(self):
        """
        Check whether or not seasons are created after running a script.
        """
        series = initial_data.create_tvseries(users=self.users)
        seasons = initial_data.create_seasons(series=series)

        self.assertSequenceEqual(
            seasons,
            models.SeasonModel.objects.all()
        )

    def test_image_creation(self):
        """
        Test helper function that creates simple test image.
        """
        image = initial_data.generate_test_image()

        self.assertIsInstance(
            image,
            files.base.ContentFile
        )

    def test_create_images_instances(self):
        """
        Check that 'create_images_instances' function attaches images to model instances.
        """
        series = initial_data.create_tvseries(self.users)
        images = initial_data.create_images_instances(series, 3)

        self.assertListEqual(
            sorted([image.pk for image in images]),
            list(models.TvSeriesModel.objects.all().values_list('images__pk', flat=True).order_by('pk')
                 ))

        self.assertEqual(
            len(images),
            len(series) * 3,
        )
