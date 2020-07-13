import datetime
import unittest

import imagehash
from django.contrib.postgres import fields as postgres_fields
from django.db import models
from rest_framework.test import APISimpleTestCase

from archives.helpers import custom_fields


class CustomFieldsPositiveTest(APISimpleTestCase):
    """
    Test for custom fields in project. Reason for test is to check how correctly 'exclude_empty_values'
    does work.
    """
    standard_JSON_field = postgres_fields.JSONField()
    standard_PositiveSmallIntegerField = models.PositiveSmallIntegerField()

    def test_custom_JSON_field_no_exclude_empty_values(self):
        """
        Check that if no arguments provided for 'exclude_empty_values' in 'CustomJSONField'
        we have same set of 'empty_values' attribute as in the standard JSONField
        """
        custom_field = custom_fields.CustomJSONField()

        self.assertSequenceEqual(
            custom_field.empty_values,
            self.standard_JSON_field.empty_values
        )

    @unittest.expectedFailure
    def test_custom_JSON_field_with_exclude_empty_values(self):
        """
        Check whether or not in case objects provided for 'exclude_empty_values' in 'CustomJSONField',
        these objects would get excluded from 'empty_values' class attribute.
        """
        custom_field = custom_fields.CustomJSONField(
            exclude_empty_values=(None, {})
        )
        self.assertSequenceEqual(
            custom_field.empty_values,
            self.standard_JSON_field.empty_values
        )

    def test_custom_PositiveSmallIntegerField_field_no_exclude_empty_values(self):
        """
        Check that if no arguments provided for 'exclude_empty_values' in 'CustomPositiveSmallIntegerField'
        we have same set of 'empty_values' attribute as in the standard PositiveSmallIntegerField
        """
        custom_field = custom_fields.CustomPositiveSmallIntegerField()

        self.assertSequenceEqual(
            custom_field.empty_values,
            self.standard_PositiveSmallIntegerField.empty_values
        )

    @unittest.expectedFailure
    def test_custom_PositiveSmallIntegerField_field_with_exclude_empty_values(self):
        """
        Check whether or not in case objects provided for 'exclude_empty_values' in 'CustomPositiveSmallIntegerField',
        these objects would get excluded from 'empty_values' class attribute.
        """
        custom_field = custom_fields.CustomPositiveSmallIntegerField(
            exclude_empty_values=(None, {})
        )
        self.assertSequenceEqual(
            custom_field.empty_values,
            self.standard_PositiveSmallIntegerField.empty_values
        )

    def test_ImageHashField(self):
        """
        Check that 'ImageHashField' successfully converts image hash to string and other way around.
        """
        field_class = custom_fields.ImageHashField
        original_string_hash = '00041dff9f101800'
        original_image_hash = imagehash.hex_to_hash(original_string_hash)

        output_string_hash = field_class(original_image_hash).get_prep_value(original_image_hash)

        self.assertEqual(
            original_string_hash,
            output_string_hash
        )

        output_image_hash = field_class(original_string_hash).to_python(original_string_hash)

        self.assertEqual(
            original_image_hash,
            output_image_hash
        )

    def test_CustomHStoreField(self):
        """
        Check that 'CustomHStoreField' converts all string numeric keys to integers on deserialization
        and iso-dates to datetime objects.
        """
        field_class = custom_fields.CustomHStoreField
        stored_dict = {'1': '2020-07-02', '2': '2020-07-02'}

        result = field_class().from_db_value(stored_dict, expression=None, connection=None)

        self.assertTrue(
            all(isinstance(key, int) for key in result.keys())
        )
        self.assertTrue(
            all(isinstance(value, datetime.date) for value in result.values())
        )
        self.assertEqual(
            len(stored_dict),
            len(result)
        )

    def test_FractionField(self):
        """
        Check that 'FractionField' correctly serialize and deserialize Fractions.
        """
        field_class = custom_fields.FractionField()
        non_serialized_data = custom_fields.Fraction(5, 6)
        serialized_data = {
                'numerator': 5,
                'denominator': 6
            }

        self.assertDictEqual(
            field_class.to_representation(non_serialized_data),
            serialized_data,
        )
        self.assertEqual(
            field_class.to_internal_value(serialized_data),
            non_serialized_data,
        )

