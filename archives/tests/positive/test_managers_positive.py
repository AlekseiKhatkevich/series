from guardian.shortcuts import assign_perm
from rest_framework.test import APITestCase

import archives.models
from archives.tests.data import initial_data
from series.constants import DEFAULT_OBJECT_LEVEL_PERMISSION_CODE
from series.helpers import test_helpers
from users.helpers import create_test_users


class ManagersPositiveTest(test_helpers.TestHelpers, APITestCase):
    """
    Test for managers and queryset custom methods in 'archives' app.
    """
    fixtures = ('users.json', 'series.json',)
    maxDiff = None

    def test_select_x_percent_top(self):
        """
        Check whether or not 'select_x_percent' method returns top x % of series
        according their rating.
        """
        percent = 40
        low_value = 6.8
        expected_queryset = archives.models.TvSeriesModel.objects.filter(
            rating__gte=low_value,
        )

        self.assertQuerysetEqual(
            archives.models.TvSeriesModel.objects.all().select_x_percent(percent, 'top'),
            expected_queryset,
            ordered=False,
            transform=lambda x: x
        )

    def test_select_x_percent_lower(self):
        """
        Check whether or not 'select_x_percent' method returns lower x % of series
        according their rating.
        """
        percent = 40
        upper_value = 5.2
        expected_queryset = archives.models.TvSeriesModel.objects.filter(
            rating__lte=upper_value,
        )

        self.assertQuerysetEqual(
            archives.models.TvSeriesModel.objects.all().select_x_percent(percent, 'bottom'),
            expected_queryset,
            ordered=False,
            transform=lambda x: x
        )

    def test_running_series(self):
        """
        Check that only series that have not finished yet are present in queryset.
        """
        running_series = archives.models.TvSeriesModel.objects.running_series()

        self.assertFalse(
            any([series.is_finished for series in running_series])
        )

    def test_finished_series(self):
        """
        Check that only series that have been finished already are present in queryset.
        """
        finished_series = archives.models.TvSeriesModel.objects.finished_series()

        self.assertTrue(
            all([series.is_finished for series in finished_series])
        )

    def test_create_relation_pair(self):
        """
        Checks that 'create_relation_pair' method of 'GroupingManager' creates pair of 'GroupingModel'
        instances and saves them in DB if 'save_in_db' flag is set to True.
        """
        from_series, to_series = archives.models.TvSeriesModel.objects.all()[:2]
        reason_for_interrelationship = 'test'

        pair_of_instances = archives.models.GroupingModel.objects.create_relation_pair(
            from_series,
            to_series,
            reason_for_interrelationship,
        )
        instance_1, instance_2 = pair_of_instances

        for instance in pair_of_instances:
            with self.subTest(instance=instance):
                self.assertIsInstance(
                    instance,
                    archives.models.GroupingModel,
                )

        self.assertEqual(
            len(pair_of_instances),
            2,
        )
        self.assertEqual(
            instance_1.from_series,
            instance_2.to_series,
        )
        self.assertEqual(
            instance_2.from_series,
            instance_1.to_series,
        )

        pair_of_instances = archives.models.GroupingModel.objects.create_relation_pair(
            from_series,
            to_series,
            reason_for_interrelationship,
            save_in_db=True,
        )
        self.assertTrue(
            archives.models.GroupingModel.objects.filter(
                pk__in=(instance.pk for instance in pair_of_instances)
            ).exists()
        )


class ManagersPositiveRegularSetupTest(test_helpers.TestHelpers, APITestCase):
    """
    Test for managers and queryset custom methods in 'archives' app.
    This one with regular setup instead of fixtures.
    """
    maxDiff = None

    def setUp(self) -> None:
        self.users = create_test_users.create_users()
        self.user_1, self.user_2, self.user_3 = self.users

        self.series = initial_data.create_tvseries(self.users)
        self.series_1, self.series_2 = self.series

    def test_annotate_with_responsible_user(self):
        """
        Check that queryset annotates with the responsible user for a series email.
        This case - user is not soft-deleted.
        """
        responsible_user_email = archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk).\
            annotate_with_responsible_user().first().responsible

        self.assertEqual(
            responsible_user_email,
            self.series_1.entry_author.email,
        )

    def test_annotate_with_responsible_user_deleted_has_master(self):
        """
        Check that queryset annotates with the responsible user for a series email.
        This case - user is soft-deleted but has master alive.
        """
        author = self.series_1.entry_author
        master = self.series_2.entry_author
        master.slaves.add(author)
        author.delete(soft_del=True)

        responsible_user_email = archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk). \
            annotate_with_responsible_user().first().responsible

        self.assertEqual(
            responsible_user_email,
            master.email,
        )

    def test_annotate_with_responsible_user_deleted_has_slaves(self):
        """
        Check that queryset annotates with the responsible user for a series email.
        This case - user is soft-deleted no master.
        """
        author = self.series_1.entry_author
        slave = self.series_2.entry_author
        author.slaves.add(slave)
        #  liberate slaves
        author.deleted = True
        author.save()

        responsible_user_email = archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk). \
            annotate_with_responsible_user().first().responsible

        self.assertEqual(
            responsible_user_email,
            slave.email,
        )

    def test_annotate_with_responsible_user_deleted_has_friends(self):
        """
        Check that queryset annotates with the responsible user for a series email.
        This case - user is soft-deleted no master, no slaves but has friend alive.
        """
        author = self.series_1.entry_author
        friend = self.series_2.entry_author
        assign_perm(DEFAULT_OBJECT_LEVEL_PERMISSION_CODE, friend, self.series_1)
        author.delete(soft_del=True)

        responsible_user_email = archives.models.TvSeriesModel.objects.filter(pk=self.series_1.pk). \
            annotate_with_responsible_user().first().responsible

        self.assertEqual(
            responsible_user_email,
            friend.email,
        )

