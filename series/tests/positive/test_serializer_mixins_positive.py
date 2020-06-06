from rest_framework import serializers
from rest_framework.test import APISimpleTestCase

from series import error_codes
from series.helpers import serializer_mixins


class SerializersMixinPositiveTest(APISimpleTestCase):
    """
    Test custom serializers mixins.
    """

    class TestSerializer(
            serializer_mixins.RequiredTogetherFieldsMixin,
            serializers.Serializer):
        field_1 = serializers.CharField(max_length=10, required=True)
        field_2 = serializers.IntegerField(required=False)
        field_3 = serializers.EmailField(required=False)

        required_together_fields = ('field_2', 'field_3',)

    def test_RequiredTogetherFieldsMixin(self):
        """
        Check whether or not 'RequiredTogetherFieldsMixin' would allow to mark set of fields as
        required together fields.
        """
        #  Fill only first required field. 2 other fields should stay non-required.
        data = {'field_1': 'test'}
        serializer = self.TestSerializer(data=data)

        self.assertTrue(
            serializer.is_valid()
        )
        self.assertFalse(
            all(field.required for field_name, field in serializer.fields.items())
        )

        #  Fill first required field and one of required_together_fields.
        #  All fields should turn required=True.
        data = {'field_1': 'test', 'field_2': 10}
        serializer = self.TestSerializer(data=data)

        self.assertFalse(
            serializer.is_valid()
        )
        self.assertTrue(
            all(field.required for field_name, field in serializer.fields.items())
        )

        # Fill all 3 fields. All fields should turn required=True.
        data = {'field_1': 'test', 'field_2': 10, 'field_3': 'email@email.com'}
        serializer = self.TestSerializer(data=data)

        self.assertTrue(
            serializer.is_valid()
        )
        self.assertTrue(
            all(field.required for field_name, field in serializer.fields.items())
        )

    class TestSerializer_2(
            serializer_mixins.ReadOnlyRaisesException,
            serializers.Serializer):
        field_1 = serializers.CharField(max_length=10, read_only=True)
        field_2 = serializers.IntegerField()
        field_3 = serializers.EmailField()

    def test_ReadOnlyRaisesException_mixin(self):
        """
        Check that in case one or more read_only fields are in initial data, serializer would
        not be validated.
        """
        data = {'field_1': 'test', 'field_2': 1, 'field_3': 'user@imbox.ru'}

        with self.assertRaisesMessage(serializers.ValidationError, error_codes.READ_ONLY.message):
            self.TestSerializer_2(data=data)

    class TestSerializer_3(
            serializer_mixins.NoneInsteadEmptyMixin,
            serializers.Serializer):
        field_1 = serializers.CharField(
            allow_null=True,
            allow_blank=True)
        field_2 = serializers.IntegerField()
        field_3 = serializers.EmailField()

        class Meta:
            none_if_empty = ('field_1', )

    def test_NoneInsteadEmptyMixin(self):
        """
        Check that 'NoneInsteadEmptyMixin' in fact changes empty containers to None.
        """
        data = {'field_1': '', 'field_2': 1, 'field_3': 'user@imbox.ru'}
        serializer = self.TestSerializer_3(data=data)
        self.assertTrue(
            serializer.is_valid()
        )
        self.assertIsNone(
            serializer.data['field_1']
        )