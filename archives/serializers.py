import guardian.models
from django.conf import settings
from django.db import transaction
from django.db.models import F, Value
from django.db.models.functions import Concat
from rest_framework import serializers

import archives.models
from series import constants
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
    if settings.IM_IN_TEST_MODE:
        image = serializers.FileField()

    class Meta:
        model = archives.models.ImageModel
        fields = ('image',)
        extra_kwargs = {
            'image': {
                'max_length': 100,
                'validators': ()
            }, }

    def create(self, validated_data):
        validated_data['content_object'] = self.context['series']
        return super().create(validated_data)


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
        read_only=True,
    )

    class Meta:
        model = archives.models.TvSeriesModel
        none_if_empty = ('interrelationship', 'images',)
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
                        ), )

            archives.models.GroupingModel.objects.bulk_create(
                list_of_interrelationships,
                ignore_conflicts=True,
            )

        return series


class SeasonShortSerializer(serializers.ModelSerializer):
    """
    Serializer on SeasonModel to use as field in TvSeriesDetailSerializer.
    """

    class Meta:
        model = archives.models.SeasonModel
        fields = ('pk', 'season_number',)
        read_only_fields = fields


class TvSeriesDetailSerializer(TvSeriesSerializer):
    """
    Serializer for retrieve, update and delete actions on Tv series.
    """
    allowed_redactors = serializers.SerializerMethodField(
    )
    seasons = SeasonShortSerializer(
        many=True,
        read_only=True,
    )

    class Meta(TvSeriesSerializer.Meta):
        fields = TvSeriesSerializer.Meta.fields + ('allowed_redactors', 'seasons',)
        keys_to_swap = ('friends', 'seasons',)

    @staticmethod
    def get_allowed_redactors(obj):
        """
        Gather information about users who have a rights to change resource.
        Only shown to object owner or admins.
        """
        # Entry creator master if exists.
        try:
            master = dict(
                pk=obj.entry_author.master_id,
                name=obj.entry_author.master.get_full_name(),
            )
        except AttributeError:
            master = None
        # Users with permissions for this entry.
        friends = guardian.models.UserObjectPermission.objects.filter(
            object_pk=obj.pk,
            content_type__model=obj.__class__.__name__.lower(),
            content_type__app_label=obj.__class__._meta.app_label.lower(),
            permission__codename=constants.DEFAULT_OBJECT_LEVEL_PERMISSION_CODE,
        ).annotate(
            friend_full_name=Concat('user__first_name', Value(' '), 'user__last_name'),
            friend_pk=F('user__pk'),
        ).values('friend_pk', 'friend_full_name', )
        # Slaves of the entry author if exists.
        slaves = [
                     {'pk': slave.pk, 'name': slave.get_full_name()}
                     for slave in obj.entry_author.slaves.all()
                 ] or None
        return dict(master=master, friends=friends, slaves=slaves)

    def get_fields(self):
        """
        Do not show to anyone except admins and object owner information about allowed object redactors.
        """
        fields = super().get_fields()
        request = self.context['request']
        entry_author = self.context['view'].obj.entry_author

        if not request.user == entry_author and not request.user.is_staff:
            fields.pop('allowed_redactors')

        return fields
