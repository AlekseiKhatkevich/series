import guardian.models
from guardian.shortcuts import assign_perm
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archives.tests.data import initial_data
from series import constants
from series.helpers import custom_functions, test_helpers
from users.helpers import create_test_users


class PermissionsListPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Positive test case on api that displays list of permissions that other users have on
    request user's objects and assignees object permissions to users.
    archives/manage-permissions/ GET, POST, DELETE <int:pk>
    """
    maxDiff = None

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

        cls.series = initial_data.create_tvseries(cls.users)

        cls.seasons = initial_data.create_seasons(cls.series)

        cls.images = initial_data.create_images_instances(cls.series)

        cls.permission_code = constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE

        cls.user_1_objects = tuple(filter(
            lambda obj: obj.entry_author == cls.user_1,
            (*cls.series, *cls.seasons, *cls.images),
        ))

    def setUp(self) -> None:
        self.permissions = []
        for obj in self.user_1_objects:
            perm = assign_perm(self.permission_code, self.user_2, obj)
            self.permissions.append(perm)

    def test_list_view(self):
        """
        Check that list action api displays list of all permission which request user has assigned
        to another users on his objects.
        archives/manage-permissions/ GET
        """
        user = self.user_1

        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse('manage-permissions-list'),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        response_dict = custom_functions.response_to_dict(response, key_field='id')

        self.assertEqual(
            len(self.user_1_objects),
            len(response.data['results']),
        )
        self.assertSetEqual(
            {int(obj['object_pk']) for obj in response_dict.values()},
            {obj.pk for obj in self.user_1_objects},
        )
        self.assertTrue(
            all([obj['user'] == self.user_2.email for obj in response_dict.values()])
        )

    def test_assign_permission(self):
        """
        Check that it is possible to assign permission on object if permission giver is an
        owner of the object and all provided data is correct.
        archives/manage-permissions/POST
        """
        user = self.user_1
        permission_receiver = self.user_3

        self.client.force_authenticate(user=user)

        for obj in self.user_1_objects:
            with self.subTest(obj=obj):
                data = dict(
                    user=permission_receiver.email,
                    model=obj.__class__._meta.model_name,
                    object_pk=obj.pk,
                )
                response = self.client.post(
                    reverse('manage-permissions-list'),
                    data=data,
                    format='json',
                )

                self.assertEqual(
                    response.status_code,
                    status.HTTP_201_CREATED,
                )

        self.assertEqual(
            guardian.models.UserObjectPermission.objects.filter(
                object_pk__int__in=[obj.pk for obj in self.user_1_objects],
                content_type__model__in=[obj.__class__._meta.model_name for obj in self.user_1_objects],
                content_type__app_label__in=[obj.__class__._meta.app_label for obj in self.user_1_objects],
                user=permission_receiver,
            ).count(),
            len(self.user_1_objects),
        )

    def test_delete(self):
        """
        Check that provided correct url permission can be deleted successfully.
        """
        permission_to_delete = self.permissions[0]
        object_owner = self.user_1

        self.client.force_authenticate(user=object_owner)

        response = self.client.delete(
            reverse('manage-permissions-detail', args=(permission_to_delete.pk, )),
            data=None,
            format='json',
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )

        self.assertFalse(
            guardian.models.UserObjectPermission.objects.filter(pk=permission_to_delete.pk).exists()
        )

