from django.core.files import images
from django.db import transaction
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
        queryset=archives.models.TvSeriesModel.objects.all()
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

    def create(self, validated_data):
        series = self.context['series']
        image = validated_data['image']
        img_instance = series.images.create(image=images.ImageFile(image))
        return img_instance


class TvSeriesSerializer(serializer_mixins.NoneInsteadEmptyMixin, serializers.ModelSerializer):
    """
    Serializer for list/create action on TvSeriesModel.
    """
    interrelationship = InterrelationshipSerializer(
        many=True,
        source='group',
        required=False,
    )
    entry_author = serializers.ReadOnlyField(
        source='entry_author.get_full_name',
    )
    request_user = serializers.HiddenField(
        default=serializers.CurrentUserDefault(),
    )
    number_of_seasons = serializers.ReadOnlyField(
        source='seasons_cnt',
    )
    number_of_episodes = serializers.ReadOnlyField(
        source='episodes_cnt',
    )
    images = ImagesSerializer(
        many=True,
        required=False
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
            'entry_author',
            'request_user',
            'interrelationship',
            'number_of_seasons',
            'number_of_episodes',
            'images',
        )
        extra_kwargs = {
            'imdb_url': {'validators': ()},
        }

    @transaction.atomic
    def create(self, validated_data):
        images_data = validated_data.pop('images', None)
        interrelationship_data = validated_data.pop('group', None)
        request_user = validated_data.pop('request_user')

        series = self.Meta.model.objects.create(
            **validated_data,
            entry_author=request_user
        )

        if interrelationship_data is not None:
            list_of_interrelationships = []
            for i_ship in interrelationship_data:
                seq = (series, i_ship['to_series'])
                for num, _ in enumerate(seq):
                    list_of_interrelationships.append(
                        archives.models.GroupingModel(
                            from_series=seq[num],
                            to_series=seq[not num],
                            reason_for_interrelationship=i_ship['reason_for_interrelationship']
                        ),)

            archives.models.GroupingModel.objects.bulk_create(
                list_of_interrelationships,
                ignore_conflicts=True,
            )

        if 'image' in (data := self.context['request'].data):
            serializer = ImagesSerializer(
                data=data,
                context={'series': series}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return series








