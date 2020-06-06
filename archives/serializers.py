from rest_framework import serializers

import archives.models

from series.helpers import serializer_mixins


class InterrelationshipSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying and creating TvSeries interrelationship series.
    """
    name = serializers.SlugRelatedField(
        source='to_series',
        slug_field='name',
        queryset=archives.models.GroupingModel.objects.all()
    )

    class Meta:
        model = archives.models.GroupingModel
        fields = ('name', 'reason_for_interrelationship',)


class ImagesSerializer(serializers.ModelSerializer):
    """
    Serializer for displaying and creating Image instances.
    """
    class Meta:
        model = archives.models.ImageModel
        fields = ('image',)
        extra_kwargs = {
            'image': {'max_length': 100}
        }


class TvSeriesSerializer(serializer_mixins.NoneInsteadEmptyMixin, serializers.ModelSerializer):
    """
    Serializer for list/create action on TvSeriesModel.
    """
    interrelationship = InterrelationshipSerializer(
        many=True,
        source='group',
        required=False,
    )
    entry_author = serializers.CharField(
        source='entry_author.get_full_name',
        read_only=True,
        default=serializers.CurrentUserDefault(),
    )
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    number_of_seasons = serializers.IntegerField(
        read_only=True,
        source='seasons_cnt',
    )
    number_of_episodes = serializers.IntegerField(
        read_only=True,
        source='episodes_cnt',
    )
    images = ImagesSerializer(
        many=True,
    )

    class Meta:
        model = archives.models.TvSeriesModel
        none_if_empty = ('interrelationship', 'images', )
        fields = (
            'pk',
            'entry_author',
            'name',
            'imdb_url',
            'is_finished',
            'rating',
            'user',
            'interrelationship',
            'number_of_seasons',
            'number_of_episodes',
            'images'
        )
        extra_kwargs = {
            'imdb_url': {'validators': ()},
        }

