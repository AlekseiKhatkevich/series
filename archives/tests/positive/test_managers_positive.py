from rest_framework.test import APITestCase

from django.db.models.functions import Floor, Ceil

import archives.models


class ManagersPositiveTest(APITestCase):
    """
    Test for managers and queryset custom methods in 'archives' app.
    """
    fixtures = ('users.json', 'series.json',)

    def test_top_x_percent(self):
        """
        Check whether or not 'top_x_percent' method returns top x % of series according their rating.
        """
        percent = 40
        value_of_one_percent = 0.08
        low_value = 6.8
        filtering_range = (6.8-10)  # their ceil and floor as rating is INT.
        expected_series_range = (Ceil(low_value), Floor(10))
        expected_queryset = archives.models.TvSeriesModel.objects.filter(
            rating__range=expected_series_range
        )

        self.assertQuerysetEqual(
            archives.models.TvSeriesModel.objects.all().top_x_percent(40),
            expected_queryset,
            ordered=False,
            transform=lambda x: x
        )

    def test_running_series(self):
        """
        Check that only series that have not finished yet are present in queryset.
        """
        full_queryset = archives.models.TvSeriesModel.objects.all()
        running_series = full_queryset.running_series()
        difference = full_queryset.difference(running_series)

        self.assertTrue(
            difference
        )
        self.assertTrue(
            difference.first().is_finished
        )
        self.assertFalse(
            any(running_series.values_list('is_finished', flat=True))
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
