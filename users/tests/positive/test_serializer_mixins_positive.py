from rest_framework.test import APISimpleTestCase
from rest_framework import serializers

from users.helpers import serializer_mixins


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
