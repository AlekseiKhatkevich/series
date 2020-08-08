from typing import Optional

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
    user = serializers.EmailField(
        source='user.email',
    )

    class Meta:
        model = administration.models.EntriesChangeLog
        fields = (
            'pk',
            'access_time',
            'as_who',
            'operation_type',
            'user',
        )


class UserHistorySerializer(serializers.ModelSerializer):
    """
    Serializer for 'UserOperationsHistoryView' in 'users' app.
    """
    model = serializers.CharField(
        source='content_type.model',
    )
    diff = serializers.JSONField(
    )

    class Meta:
        model = administration.models.EntriesChangeLog
        exclude = (
            'content_type',
            'user',
            'state',
        )


class HistoryDetailSerializer(HistorySerializer):
    """
    Serializer for 'EntriesChangeLog' model in detail views of 'HistoryViewSet'.
    """
    prev_state = serializers.JSONField(
    )
    prev_changes = serializers.SerializerMethodField(
    )
    next_state = serializers.JSONField(
    )
    next_changes = serializers.SerializerMethodField(
    )

    class Meta:
        model = administration.models.EntriesChangeLog
        fields = (
            'pk',
            'access_time',
            'as_who',
            'operation_type',
            'user',
            'prev_state',
            'state',
            'next_state',
            'prev_changes',
            'next_changes',
        )

    def get_prev_changes(self, obj: Meta.model) -> Optional[set]:
        """
        Returns changes in 'state' between current state and previous state.
        """
        return self.calculate_difference(obj.state, prev_state=obj.prev_state)

    def get_next_changes(self, obj: Meta.model) -> Optional[set]:
        """
        Returns changes in 'state' between current state and next state.
        """
        return self.calculate_difference(obj.state, next_state=obj.next_state)

    @staticmethod
    def calculate_difference(
            state: dict,
            *,
            prev_state: dict = None,
            next_state: dict = None,
    ) -> Optional[set]:
        """
        Calculates a difference between 2 states.
        """
        assert not (prev_state and next_state),\
            'Need to have either "prev_state" or "next_state", not both simultaneously.'

        next_or_prev_state = prev_state or next_state
        if next_or_prev_state is None:
            return None

        changed_keys = set()

        for (key, next_or_prev_state_val), (key, curr_val) in zip(next_or_prev_state.items(), state.items()):
            if next_or_prev_state_val != curr_val:
                changed_keys.add(key)

        return changed_keys or None


