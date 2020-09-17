import tempfile

from django.core import exceptions
from django.core.files.base import File
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series import error_codes
from users.helpers import create_test_users


class ImageModelNegativeTest(APITestCase):
    """
    Negative test on 'ImageModel'.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series_1, *tail = initial_data.create_tvseries(users=cls.users)

        cls.test_image = initial_data.generate_test_image()

    def test_create_model_instance_with_wrong_file_type(self):
        """
        Check that if any other file type apart of image files would be used to save in model, then
        exception would be arisen.
        """
        expected_error_message = error_codes.NOT_AN_IMAGE.message

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            with tempfile.NamedTemporaryFile() as fake_image_file:
                self.series_1.images.create(
                    image=File(fake_image_file),
                )

    def test_len_16_constraint(self):
        """
        Check that only image hash value consisted from 16 characters are allowed to be saved in 'DB'.
        """
        expected_error_message = 'len_16_constraint'

        image = archives.models.ImageModel.objects.create(
            image=self.test_image,
            content_object=self.series_1,
            entry_author=self.user_3,
            fc=False
        )

        with self.assertRaisesMessage(IntegrityError, expected_error_message):
            archives.models.ImageModel.objects.filter(pk=image.pk).update(image_hash=12345)

    def test_save_same_image(self):
        """
        Check that same or similar image can't be saved twice.
        """
        expected_error_message = error_codes.IMAGE_ALREADY_EXISTS.message

        with self.assertRaisesMessage(exceptions.ValidationError, expected_error_message):
            for _ in range(2):
                archives.models.ImageModel.objects.create(
                    image=self.test_image,
                    content_object=self.series_1,
                    entry_author=self.user_3,
                )
