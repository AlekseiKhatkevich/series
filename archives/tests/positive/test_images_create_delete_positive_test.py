import operator
import os

import more_itertools
from django.conf import settings
from django.core.files import File
from guardian.shortcuts import assign_perm, remove_perm
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series.helpers import test_helpers
from users.helpers import create_test_users


class ImagesCreatePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on images upload/create api endpoint.
    /tvseries/{1}/upload-image/{2}/ POST
    1 - id of the series; 2 - image file filename with extension.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

        cls.image = initial_data.generate_test_image()

        test_images_path = os.path.join(settings.MEDIA_ROOT, 'images_for_tests', 'real_test_image.jpg')
        with open(test_images_path, 'rb') as image_file:
            cls.real_image = File(image_file)

    @test_helpers.switch_off_validator('IsImageValidator')
    def test_upload_image(self):
        data = {'file': self.image}
        user = self.series_1.entry_author
        filename = 'small_image.gif'
        expected_image_file_path = os.path.join(
            settings.MEDIA_ROOT,
            self.series_1.name,
            filename,
        )
        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse('upload', args=[self.series_1.pk, filename]),
            data=data,
            format='gif',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertTrue(
            self.series_1.images.all().exists()
        )
        self.assertTrue(
            os.path.exists(expected_image_file_path)
        )


class ImageDeletePositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test on images delete api endpoint.
    tvseries/<int:series_pk>/delete-image/<int_list:image_pk>/ DELETE
    """

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

    def test_slave_deletes_images(self):
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

    def test_master_deletes_images(self):
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

    def test_user_with_a_guardian_permission_deletes_image(self):
        """
        Check tha user with proper guardian permission is able to delete image.
        """
        test_user = more_itertools.first_true(
            iterable=self.users,
            pred=lambda user: user != self.series_1.entry_author and not user.is_superuser,
        )
        assign_perm('permissiveness', test_user, self.series_1)

        self.client.force_authenticate(user=test_user)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        remove_perm('permissiveness', test_user, self.series_1)