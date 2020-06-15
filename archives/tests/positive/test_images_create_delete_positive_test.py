import operator

from django.conf import settings
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


# todo
class ImagesCreatePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on images upload/create api endpoint.
    /tvseries/{1}/upload-image/{2}/ POST
    1 - id of the series; 2 - image file filename with extension.
    """
    pass


class ImageDeletePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on images delete api endpoint.
    tvseries/<int:series_pk>/delete-image/<int_list:image_pk>/ DELETE
    """

    original_media_root = settings.MEDIA_ROOT

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.images = initial_data.create_images_instances(self.series, 2)
        self.series_1_images_pks = map(
            operator.attrgetter('pk'),
            filter(
                lambda img: img.object_id == self.series_1.pk,
                self.images)
        )

    def test_delete_images(self):
        """
        Check that if correct input data is provided, then chosen 'ImageModel' instances would be
        deleted from DB.
        """
        user = self.series_1.entry_author
        expected_success_message = {"Number_of_deleted_images": 2}

        self.client.force_authenticate(user=user)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT
        )
        self.assertDictEqual(
            response.data,
            expected_success_message,
        )
        self.assertFalse(
            self.series_1.images.all().exists()
        )

    def test_slave_delete_images(self):
        """
        Check that slave of the series entry author is able to delete images.
        """
        user = self.series_1.entry_author
        slave = self.user_2
        user.slaves.add(slave)

        self.client.force_authenticate(user=slave)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_master_delete_images(self):
        """
        Check that master of the series entry author is able to delete images.
        """
        user = self.series_1.entry_author
        master = self.user_2
        master.slaves.add(user)

        self.client.force_authenticate(user=master)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

