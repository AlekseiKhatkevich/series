from guardian.shortcuts import assign_perm
from rest_framework import fields, status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import constants, error_codes
from series.helpers import test_helpers
from users.helpers import create_test_users


class PermissionsListNegativeTest(test_helpers.TestHelpers, APITestCase):
    """
    Negative test case on api that displays list of permissions that other users have on
    request user's objects and assignees object permissions to users.
    archives/manage-permissions/ GET, POST, DELETE <int:pk>
    """
    maxDiff = None

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)

        self.seasons, self.seasons_dict = initial_data.create_seasons(self.series, return_sorted=True)

        self.images = initial_data.create_images_instances(self.series)

        self.user_1_objects = tuple(filter(
            lambda obj: obj.entry_author == self.user_1,
            (*self.series, *self.seasons, *self.images),
        ))

    def test_user_does_not_exists(self):
        """
        Check that exception is raised if permission received user does not exists.
        """
        expected_error_message = error_codes.USER_DOESNT_EXISTS.message
        permission_giver = self.user_1
        obj = self.user_1_objects[0]
        data = dict(
            user='fake@email.com',
            model=obj.__class__._meta.model_name,
            object_pk=obj.pk,
        )

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='user',
        )

    def test_model_choices(self):
        """
        Check that wrong model choices would raise an exception.
        """
        permission_giver = self.user_1
        permission_receiver = self.user_3
        obj = self.user_1_objects[0]
        fake_model_name = 'fake-model'
        data = dict(
            user=permission_receiver.email,
            model=fake_model_name,
            object_pk=obj.pk,
        )
        expected_error_message = fields.ChoiceField.default_error_messages['invalid_choice'].\
            format(input=fake_model_name)

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='model',
        )

    def test_assign_permission_to_self(self):
        """
        Check that user can not assign permission to himself.
        """
        permission_giver = permission_receiver = self.user_1
        obj = self.user_1_objects[0]
        data = dict(
            user=permission_receiver.email,
            model=obj.__class__._meta.model_name,
            object_pk=obj.pk,
        )
        expected_error_message = error_codes.PERM_TO_SELF.message

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='user',
        )

    def test_assign_permission_to_master(self):
        """
        Check that user can not assign permission to his master.
        """
        permission_giver = self.user_1
        permission_receiver = self.user_3
        permission_receiver.slaves.add(permission_giver)
        obj = self.user_1_objects[0]
        data = dict(
            user=permission_receiver.email,
            model=obj.__class__._meta.model_name,
            object_pk=obj.pk,
        )
        expected_error_message = error_codes.PERM_TO_MASTER.message

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='user',
        )

    def test_assign_permission_to_slave(self):
        """
        Check that user can not assign permission to his slave.
        """
        permission_giver = self.user_1
        permission_receiver = self.user_3
        permission_giver.slaves.add(permission_receiver)
        obj = self.user_1_objects[0]
        data = dict(
            user=permission_receiver.email,
            model=obj.__class__._meta.model_name,
            object_pk=obj.pk,
        )
        expected_error_message = error_codes.PERM_TO_SLAVE.message

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='user',
        )

    def test_model_instance_does_not_exists(self):
        """
        Check that if model instance does not exist, than exception should be arisen.
        """
        permission_giver = self.user_1
        permission_receiver = self.user_3
        obj = self.user_1_objects[0]
        data = dict(
            user=permission_receiver.email,
            model=obj.__class__._meta.model_name,
            object_pk=999999999999999,
        )
        expected_error_message = error_codes.OBJECT_NOT_EXISTS.message

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='object_pk',
        )

    def test_entry_author_ne_request_user(self):
        """
        Check that only object's author can assign permissions.
        """
        permission_giver = self.user_2
        permission_receiver = self.user_3
        obj = self.user_1_objects[0]
        data = dict(
            user=permission_receiver.email,
            model=obj.__class__._meta.model_name,
            object_pk=obj.pk,
        )
        expected_error_message = error_codes.USER_NOT_AUTHOR.message

        self.client.force_authenticate(user=permission_giver)

        response = self.client.post(
            reverse('manage-permissions-list'),
            data=data,
            format='json',
        )

        self.check_status_and_error_message(
            response,
            error_message=expected_error_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            field='user',
        )

    def test_delete(self):
        """
        Check that user can't delete permission on object that belongs not to him.
        """
        not_object_owner = self.user_2
        permission_to_delete = assign_perm(
            constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE,
            self.user_3,
            self.user_1_objects[0],
        )

        self.client.force_authenticate(user=not_object_owner)

        response = self.client.delete(
            reverse('manage-permissions-detail', args=(permission_to_delete.pk,)),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

        self.assertTrue(
            permission_to_delete.__class__.objects.filter(pk=permission_to_delete.pk).exists()
        )
