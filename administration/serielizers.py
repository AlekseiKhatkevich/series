from django_db_logger.models import StatusLog
from rest_framework import serializers
import administration.models


class LogsSerializer(serializers.ModelSerializer):
    """
    Serializer for logs stored in DB.
    """
    level = serializers.ReadOnlyField(
        source='get_level_display',
    )

    class Meta:
        model = StatusLog
        exclude = ('id', )


class HistorySerializer(serializers.ModelSerializer):
    """
    Serializer for 'EntriesChangeLog' model.
    """
    user = serializers.ReadOnlyField(
        source='user.email',
    )

    class Meta:
        model = administration.models.EntriesChangeLog
        fields = ('pk', 'access_time', 'as_who', 'operation_type', 'user', )

