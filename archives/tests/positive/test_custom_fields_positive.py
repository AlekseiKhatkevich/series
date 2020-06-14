import unittest

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