import operator

from django.conf import settings
from rest_framework import status, exceptions as drf_exceptions
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class ImagesCreateNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test on images upload/create api endpoint.
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

    def test_not_binary_mode_upload(self):
        """
        Check that if upload happens in non-binary mode, then exception would be arisen.
        """
        data = None
        user = self.series_1.entry_author
        filename = 'small_image.gif'

        self.client.force_authenticate(user=user)

        response = self.client.post(
            reverse('upload', args=[self.series_1.pk, filename]),
            data=data,
            format='gif',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_message=error_codes.NOT_A_BINARY.message,
            field=None,
        )


class ImageDeleteNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test on images delete api endpoint.
    tvseries/<int:series_pk>/delete-image/<int_list:image_pk>/ DELETE
    """

    original_media_root = settings.MEDIA_ROOT

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, *rest = cls.users

        cls.series = initial_data.create_tvseries(cls.users)
        cls.series_1, cls.series_2 = cls.series

    def setUp(self) -> None:
        self.images = initial_data.create_images_instances(self.series, user=self.user_1, num_img=2,)
        self.series_1_images_pks = map(
            operator.attrgetter('pk'),
            filter(
                lambda img: img.object_id == self.series_1.pk,
                self.images)
        )

    def test_validate_image_to_delete_method(self):
        """
        Check that 'validate_images_to_delete' method correctly raises en exception when at least
        on of a images pks being passed via url is not belong to series images.
        """
        user = self.series_1.entry_author
        wrong_image_pks = (1000, 999)
        expected_error_message = \
            f'Images with pk {" ,".join(map(str, wrong_image_pks))} does not exist in the database.'

        self.client.force_authenticate(user=user)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, wrong_image_pks]),
            data=None,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_400_BAD_REQUEST,
            field=None,
            error_message=expected_error_message,
        )

    def test_MasterSlaveRelations_permissions_anonymous(self):
        """
        Check that anonymous user can not access API endpoint.
        """
        expected_error_message = 'Authentication credentials were not provided.'

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=expected_error_message,
        )

    def test_MasterSlaveRelations_permissions_not_master_or_slave(self):
        """
        Check that not a series creator, not a series creator slave or master
        can not access API endpoint.
        """
        expected_error_message = drf_exceptions.PermissionDenied.default_detail
        wrong_user = self.series_2.entry_author

        self.client.force_authenticate(user=wrong_user)

        response = self.client.delete(
            reverse('delete-image', args=[self.series_1.pk, self.series_1_images_pks]),
            data=None,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            status_code=status.HTTP_403_FORBIDDEN,
            error_message=expected_error_message,
        )
