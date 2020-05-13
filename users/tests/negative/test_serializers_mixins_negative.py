from rest_framework.test import APISimpleTestCase
from rest_framework import serializers

from users.helpers import serializer_mixins

from series import error_codes


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

