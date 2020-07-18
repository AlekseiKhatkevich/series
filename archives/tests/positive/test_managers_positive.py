from rest_framework.test import APITestCase

import archives.models


class ManagersPositiveTest(APITestCase):
    """
    Test for managers and queryset custom methods in 'archives' app.
    """
    fixtures = ('users.json', 'series.json',)

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
