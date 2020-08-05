import json

from rest_framework.test import APITestCase

from administration import encoders
from archives import models as archive_models
from archives.helpers.custom_functions import create_image_hash, daterange
from archives.tests.data import initial_data
from archives.tests.data.initial_data import generate_test_image
from users.helpers import create_test_users


class EncodersPositiveTest(APITestCase):
    """
    Positive tests on 'administration' app encoders.
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_CustomEncoder_daterange(self):
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

    def test_CustomEncoder_model(self):
        """
        Check that 'CustomEncoder' correctly encodes model instance.
        """
        expected_result = self.user_1.pk
        model_instance = self.user_1

        actual_result = encoders.CustomEncoder().encode(model_instance)

        self.assertJSONEqual(
            actual_result,
            expected_result,
        )

    def test_CustomEncoder_ImageFieldFile(self):
        """
        Check that 'CustomEncoder' correctly encodes ImageFieldFile instance.
        """
        raw_image = initial_data.generate_test_image()
        test_image_instance = archive_models.ImageModel(
            image=raw_image,
            image_hash=1111111111111111,
            content_object=self.user_1
        )

        image_field_file_instance = test_image_instance.image

        expected_result = json.dumps(str(image_field_file_instance))
        actual_result = encoders.CustomEncoder().encode(image_field_file_instance)

        self.assertJSONEqual(
            actual_result,
            expected_result,
        )

    def test_CustomEncoder_ImageHash(self):
        """
        Check that 'CustomEncoder' correctly encodes ImageHash instance.
        """
        image = generate_test_image()
        image_hash = create_image_hash(image)

        result = encoders.CustomEncoder().encode(image_hash)

        self.assertIsInstance(
            result,
            str,
        )
