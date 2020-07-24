from django_db_logger.models import StatusLog
from rest_framework import serializers


class LogsSerializer(serializers.ModelSerializer):
    """
    Serializer for logs stored in DB.
    """
    level = serializers.ReadOnlyField(source='get_level_display')

    class Meta:
        model = StatusLog
        exclude = ('id', )
