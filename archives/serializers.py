from rest_framework import serializers

import archives.models


class InterrelationshipSerializer(serializers.ModelSerializer):
    """

    """
    name = serializers.CharField(source='from_series.name', read_only=True)

    class Meta:
        model = archives.models.GroupingModel
        fields = ('name', 'reason_for_interrelationship',)
        extra_kwargs = {
        }


class TvSeriesSerializer(serializers.ModelSerializer):
    """
    Serializer for list/create action on TvSeriesModel.
    """
    interrelationship = InterrelationshipSerializer(
        many=True,
        source='group',
        allow_null=True,
    )
    entry_author = serializers.CharField(
        source='entry_author.get_full_name',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        model = archives.models.TvSeriesModel
        fields = (
            'pk',
            'entry_author',
            'name',
            'imdb_url',
            'is_finished',
            'rating',
            'user',
            'interrelationship'
        )
        extra_kwargs = {
            'imdb_url': {'validators': ()},
        }
