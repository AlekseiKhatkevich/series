from rest_framework.test import APITestCase

from django.contrib.auth import get_user_model

from users.helpers import create_test_users

from django.db.models import Q


class UserManagerAndQuerysetPositiveTest(APITestCase):
    """
    Test for User model manager and queryset methods.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, cls.user_2, cls.user_3 = cls.users

    def test_get_available_slaves(self):
        """
         Check that method 'get_available_slaves'of User model queryset returns queryset with
         only available slaves.
        """
        self.user_3.master = self.user_1
        self.user_3.save()

        #  only user_2 is available slave.
        with self.assertNumQueries(2):
            self.assertQuerysetEqual(
                get_user_model().objects.get_available_slaves(),
                get_user_model().objects.filter(email=self.user_2.email),
                ordered=False,
                transform=lambda x: x
            )

    def test_check_user_and_password_method(self):
        """
        Check whether or not method 'check_user_and_password' returns user instance provided that correct
        input data has been received.
        """
        self.user_1.set_password('secret')
        self.user_1.save()

        user = get_user_model().objects.check_user_and_password(
            email=self.user_1.email,
            password='secret'

        )
        self.assertEqual(
            self.user_1,
            user
        )

    def test_check_user_and_password_method_with_soft_deleted_user(self):
        """
        Check that if flag 'include_soft_deleted' set to True in method 'check_user_and_password',
        then soft-deleted user would not be found and error would be arisen.
        """
        self.user_1.set_password('secret')
        self.user_1.save()
        self.user_1.delete(soft_del=True)

        user = get_user_model().objects.check_user_and_password(
            email=self.user_1.email,
            password='secret',
            include_soft_deleted=True,
        )
        self.assertEqual(
            self.user_1,
            user
        )

    def test_queryset_delete_method(self):
        """
        Check that queryset 'delete' method if called with argument 'soft_del=True' soft-deletes
        models instances in queryset rather then delete them in real. And other way around.
        """
        get_user_model().objects.all().delete(soft_del=True)
        self.assertFalse(
            get_user_model().all_objects.filter(
                Q(deleted_time__isnull=True) | Q(deleted=False)).exists()
        )

        get_user_model()._default_manager.all().update(deleted=False)
        get_user_model().objects.all().delete(soft_del=False)

        self.assertFalse(
            get_user_model()._default_manager.all().exists()
        )

    def test_undelete(self):
        """
        Check that soft-deleted user instances get undeleted after calling method 'undelete' on them.
        """
        get_user_model().objects.all().delete(soft_del=True)
        get_user_model().all_objects.all().undelete()
        self.assertCountEqual(
            self.users,
            get_user_model().objects.all()
        )

    def test_is_soft_deleted(self):
        """
        Checks whether or not user with given email is soft-deleted.
        """
        self.user_1.delete()

        self.assertTrue(
            get_user_model().objects.is_soft_deleted(email=self.user_1.email)
        )
