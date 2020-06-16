import tempfile

from rest_framework.test import APISimpleTestCase

from archives.helpers import custom_functions


class CustomFunctionsNegativeTest(APISimpleTestCase):
    """
    Negative tests for custom functions in 'archives' app.
    """

    def test_create_image_hash_with_wrong_image_file(self):
        """
        Check that if 'raise_errors' flag is True, then in case 'create_image_hash' function receives
        non-image file, exception would be arisen.
        """
        with self.assertRaises(custom_functions.PIL.UnidentifiedImageError):
            with tempfile.TemporaryFile() as file:
                custom_functions.create_image_hash(file, raise_errors=True)

    def test_create_image_hash_with_wrong_image_file_no_errors(self):
        """
        Check that if 'raise_errors' flag is False, then in case 'create_image_hash' function receives
        non-image file, then None would be returned.
        """
        with tempfile.TemporaryFile() as file:
            image_hash = custom_functions.create_image_hash(file, raise_errors=False)

        self.assertIsNone(
            image_hash
        )