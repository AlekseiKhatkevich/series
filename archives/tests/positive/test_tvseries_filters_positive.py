import datetime

from django.http import QueryDict
from psycopg2.extras import DateRange
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

import archives.filters
import archives.models
from archives.helpers.custom_functions import daterange
from archives.tests.data import initial_data
from series.helpers import custom_functions
from users.helpers import create_test_users


class FiltersPositiveTest(APITestCase):
    """
    Positive test on 'archives' TvseriesModel list view api.
    """

    @classmethod
    def setUpTestData(cls):
        cls.users = create_test_users.create_users()
        cls.user_1, *rest = cls.users

    def setUp(self) -> None:
        self.series = initial_data.create_tvseries(users=self.users)
        self.series_1, self.series_2 = self.series

        self.seasons = initial_data.create_seasons(series=self.series)
        self.season_1_1, self.season_1_2, self.season_2_1, self.season_2_2 = self.seasons

        self.query_dict = QueryDict(mutable=True)
        self.query_dict_2 = QueryDict(mutable=True)

    def test_DateExactRangeField(self):
        """
        Check that 'DateExactRangeField' field converts 2 ISO dates to DateRange.
        """
        iso_date_1 = "2012-01-01"
        iso_date_2 = "2015-01-01"
        field = archives.filters.DateExactRangeField()

        date_range = field.compress([iso_date_1, iso_date_2])

        self.assertIsInstance(
            date_range,
            DateRange,
        )
        self.assertListEqual(
            [datetime.date.fromisoformat(date) for date in (iso_date_1, iso_date_2)],
            [date_range.lower, date_range.upper],
        )

    def test_is_empty(self):
        """
        Check that 'is_empty' filter returns only empty series.
        """
        self.series_1.seasons.all().delete()
        self.query_dict['is_empty'] = True

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('tvseries') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )
        response_dict = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(
            any([season['number_of_seasons'] for season in response_dict.values()])
        )

    def test_is_finished(self):
        """
         Check that 'is_finished' filter returns only finished series.
        """
        self.series_2.translation_years = daterange((2012, 1, 1), None)
        self.series_2.save(update_fields=('translation_years',))
        self.query_dict['is_finished'] = True

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('tvseries') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )

        response_dict = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertTrue(
            all([season['is_finished'] for season in response_dict.values()])
        )

    def test_translation_years_contained_by(self):
        """
        Check that 'translation_years_contained_by' filter returns only series contained inside chosen range.
        Check that 'translation_years_overlap' returns only series with a daterange that overlaps
        over chosen range.
        """
        self.query_dict['translation_years_contained_by_upper'] = '2014-12-31'
        self.query_dict['translation_years_contained_by_lower'] = '2011-1-1'

        self.query_dict_2['translation_years_overlap_upper'] = '2013-01-01'
        self.query_dict_2['translation_years_overlap_lower'] = '2011-1-1'

        self.client.force_authenticate(user=self.user_1)

        for dictionary in (self.query_dict, self.query_dict_2):
            with self.subTest(dictionary=dictionary):
                response = self.client.get(
                    reverse('tvseries') + '?' + dictionary.urlencode(),
                    data=None,
                    format='json',
                )

                response_dict = custom_functions.response_to_dict(response, key_field='pk')

                self.assertEqual(
                    response.status_code,
                    status.HTTP_200_OK,
                )
                self.assertEqual(
                    len(response_dict),
                    1
                )
                self.assertIn(
                    self.series_1.pk,
                    response_dict.keys()
                )

    def test_TopBottomPercentField(self):
        """
        Check that 'TopBottomPercentField' field converts input value to dict.
        """
        field = archives.filters.TopBottomPercentField()
        data_list = ['top', 10]
        expected_output_dict = dict(
            position='top',
            percent=10,
        )

        output_dict = field.compress(data_list)

        self.assertDictEqual(
            expected_output_dict,
            output_dict,
        )

    def test_series_percent(self):
        """
        Check that 'series_percent' filter returns queryset filtered by top or bottom x % by rating.
        """
        self.query_dict['series_percent_position'] = 'top'
        self.query_dict['series_percent_percent'] = 30
        expected_queryset = archives.models.TvSeriesModel.objects.all().select_x_percent(30, 'top')

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(
            reverse('tvseries') + '?' + self.query_dict.urlencode(),
            data=None,
            format='json',
        )

        response_dict = custom_functions.response_to_dict(response, key_field='pk')

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertNotEqual(
            len(response_dict),
            len(self.series)
        )
        self.assertListEqual(
            list(response_dict.keys()),
            list(expected_queryset.values_list('pk', flat=True))
        )
