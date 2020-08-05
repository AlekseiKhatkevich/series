import os

import imagehash
from django.conf import settings
from rest_framework.test import APITestCase

from archives import models as archive_models
from archives.tests.data import initial_data
from users.helpers import create_test_users


class ImageModelPositiveTest(APITestCase):
    """
    Test for 'ImageModel' instance smooth creation if proper set of data is provided.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, *rest = cls.users

        cls.series = initial_data.create_tvseries(users=cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.seasons = initial_data.create_seasons(series=cls.series)
        cls.season_1, *tail = cls.seasons

        cls.raw_image = initial_data.generate_test_image()
        cls.test_image_instance = cls.series_1.images.create(
            image=cls.raw_image,
            fc=False,
            image_hash=1111111111111111,
            entry_author=cls.user_1
        )

    def test_file_upload_function_tvseriesmodel(self):
        """
        Check if when 'ImageModel' instance attached via generic FK to different primary models,
        then uploaded images are saved with different paths in different folders.
        This one with 'TvSeriesModel'.
        """
        image_model_instance = self.test_image_instance

        expected_file_path = os.path.join(
            settings.BASE_DIR,
            settings.MEDIA_ROOT,
            image_model_instance.content_object.name,
            image_model_instance.image_file_name
        )
        normalized_expected_path = os.path.normpath(expected_file_path)

        self.assertEqual(
            os.path.normpath(image_model_instance.image.path),
            normalized_expected_path
             )

    def test_file_upload_function_seasonmodel(self):
        """
        Check if when 'ImageModel' instance attached via generic FK to different primary models,
        then uploaded images are saved with different paths in different folders.
        This one with 'SeasonModel'.
        """
        image_model_instance = archive_models.ImageModel.objects.create(
            image=self.raw_image,
            content_object=self.season_1,
            entry_author=self.user_1,
            fc=False,
        )

        expected_file_path = os.path.join(
            settings.BASE_DIR,
            settings.MEDIA_ROOT,
            image_model_instance.content_object.series.name,
            str(image_model_instance.content_object.season_number),
            image_model_instance.image_file_name,
        )
        normalized_expected_path = os.path.normpath(expected_file_path)

        self.assertEqual(
            os.path.normpath(image_model_instance.image.path),
            normalized_expected_path
             )

    def test_file_upload_function_any_other_model(self):
        """
        Check if when 'ImageModel' instance attached via generic FK to different primary models,
        then uploaded images are saved with different paths in different folders.
        This one with any random model ('users.User' in this exact test).
        """
        image_model_instance = archive_models.ImageModel.objects.create(
            image=self.raw_image,
            content_object=self.users[0],
            entry_author=self.user_1,
            fc=False,
        )

        expected_file_path = os.path.join(
            settings.BASE_DIR,
            settings.MEDIA_ROOT,
            'uploads/images/',
            image_model_instance.image_file_name,
        )
        normalized_expected_path = os.path.normpath(expected_file_path)

        self.assertEqual(
            os.path.normpath(image_model_instance.image.path),
            normalized_expected_path
             )

    def test_str_(self):
        """
        Check correct work of string representation.
        """
        expected_str = f'image - {self.test_image_instance.image.name},' \
                       f' model - {self.test_image_instance.content_type} ' \
                       f'- pk={self.test_image_instance.object_id}'

        self.assertEqual(
            self.test_image_instance.__str__(),
            expected_str,
        )

    def test_image_file_name_property(self):
        """
        Check whether or not 'image_file_name' returns image filename.
        """
        expected_result = os.path.basename(self.test_image_instance.image.file.name)

        self.assertEqual(
            self.test_image_instance.image_file_name,
            expected_result
        )

    def test_image_hash(self):
        """
        Check that during model instance creation image_hash would be created and written in DB as well.
        """
        test_image_instance = self.series_1.images.create(
                image=initial_data.generate_test_image(),
                entry_author=self.user_1,
                fc=False,
        )
        test_image_instance.refresh_from_db()

        self.assertIsInstance(
            test_image_instance.image_hash,
            imagehash.ImageHash,
        )
