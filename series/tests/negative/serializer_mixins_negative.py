from rest_framework import serializers
from rest_framework.test import APISimpleTestCase

from series import error_codes
from series.helpers import serializer_mixins


class SerializersMixinNegativeTest(APISimpleTestCase):
    """
    Test error handling in custom serializers mixins.
    """

    class TestSerializer(
        serializer_mixins.RequiredTogetherFieldsMixin,
        serializers.Serializer):
        field_1 = serializers.CharField(max_length=10, required=True)
        field_2 = serializers.IntegerField(required=False)
        field_3 = serializers.EmailField(required=False)

        required_together_fields = ('field_2', 'field_3', 'wrong_field')

    def test_required_together_fields_have_wrong_field(self):
        """
        Check if exception is conjured up if we place wrong field name in 'required_together_fields'
        """
        expected_error_message = error_codes.REQUIRED_TOGETHER_WRONG_FIELDS_NAMES.message

        with self.assertRaisesMessage(serializers.ValidationError, expected_error_message):
            self.TestSerializer()

    class TestSerializer_3(
        serializer_mixins.NoneInsteadEmptyMixin,
        serializers.Serializer):
        field_1 = serializers.CharField(
            allow_null=True,
            allow_blank=True)
        field_2 = serializers.IntegerField()
        field_3 = serializers.EmailField()

        class Meta:
            none_if_empty = ('fake_field',)

    def test_NoneInsteadEmptyMixin_assertion(self):
        """
        Check that 'NoneInsteadEmptyMixin' raises assertion error in case wrong field name is provided
        in 'none_if_empty' Meta attribute.
        """
        data = {'field_1': '', 'field_2': 1, 'field_3': 'user@imbox.ru'}
        expected_error_message = \
            f'Fields {set(("fake_field", ))} do not belong to serializer "{self.TestSerializer_3.__name__}"'

        with self.assertRaisesMessage(AssertionError, expected_error_message):
            serializer = self.TestSerializer_3(data=data)
            self.assertTrue(
                serializer.is_valid()
            )
            self.assertIsNone(
                serializer.data['field_1']
            )
