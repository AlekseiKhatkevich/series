import guardian.models
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F, Q, TextChoices, Value
from django.db.models.functions import Concat
from django.utils import timezone
from drf_extra_fields.fields import DateRangeField
from guardian.shortcuts import assign_perm
from rest_framework import permissions, serializers

import archives.models
from archives.helpers import custom_fields
from series import constants, error_codes
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
        validated_data['entry_author'] = self.context['request'].user
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
    translation_years = DateRangeField(
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
            'translation_years',
            'rating',
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
                pair = archives.models.GroupingModel.objects.create_relation_pair(
                    from_series=series,
                    to_series=i_ship['to_series'],
                    reason_for_interrelationship=i_ship['reason_for_interrelationship'],
                )
                list_of_interrelationships += pair

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


class TvSeriesDetailSerializer(serializer_mixins.ReadOnlyRaisesException, TvSeriesSerializer):
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

    @transaction.atomic
    def update(self, instance, validated_data):
        interrelationship_data = validated_data.pop('group', None)
        series = super().update(instance, validated_data)

        if interrelationship_data is not None:
            #  Create model instances for incoming interrelationships.
            list_of_interrelationships = []
            for i_ship in interrelationship_data:
                pair = archives.models.GroupingModel.objects.create_relation_pair(
                    from_series=series,
                    to_series=i_ship['to_series'],
                    reason_for_interrelationship=i_ship['reason_for_interrelationship'],
                )
                list_of_interrelationships += pair
            # All interrelationships intermediate model instances for series.
            qs = archives.models.GroupingModel.objects.filter(
                Q(from_series=series) | Q(to_series=series)
            )
            # Interrelationships intermediate model instances that must be deleted.
            to_delete = set(qs).difference(list_of_interrelationships)
            # Interrelationships intermediate model instances that must be created.
            new = set(list_of_interrelationships).difference(qs)

            if to_delete:
                qs.filter(pk__in=(group.pk for group in to_delete)).delete()

            if new:
                archives.models.GroupingModel.objects.bulk_create(
                    list_of_interrelationships,
                    ignore_conflicts=True,
                )
        return series

    def get_fields(self):
        """
        Do not show to anyone except admins and object owner information about allowed object redactors.
        """
        fields = super().get_fields()
        request = self.context['request']
        entry_author = self.context['view'].get_object().entry_author

        if (not request.user == entry_author and not request.user.is_staff) or \
                request.method not in permissions.SAFE_METHODS:
            fields.pop('allowed_redactors')

        return fields

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


class SeasonsSerializer(serializer_mixins.ReadOnlyRaisesException, serializers.ModelSerializer):
    """
    Serializer for SeasonModel list/create action.
    """
    translation_years = DateRangeField(
    )
    progress = custom_fields.FractionField(
        read_only=True,
    )
    entry_author = serializers.ReadOnlyField(
        source='entry_author.get_full_name',
    )

    class Meta:
        model = archives.models.SeasonModel
        fields = (
            'pk',
            'season_number',
            'last_watched_episode',
            'number_of_episodes',
            'episodes',
            'translation_years',
            'is_fully_watched',
            'is_finished',
            'progress',
            'new_episode_this_week',
            'entry_author'
        )
        extra_kwargs = {
            'season_number': {
                'required': True,
            }, }

    def create(self, validated_data):
        request = self.context['request']
        view = self.context['view']

        validated_data['entry_author'] = request.user
        validated_data['series'] = view.series

        return super().create(validated_data)


class DetailSeasonSerializer(SeasonsSerializer):
    """
    Serializer for seasons detail action.
    """
    series_name = serializers.SerializerMethodField(
    )
    days_until_free_access = serializers.SerializerMethodField(
    )

    class Meta(SeasonsSerializer.Meta):
        fields = SeasonsSerializer.Meta.fields + ('series_name', 'days_until_free_access',)

    @staticmethod
    def get_days_until_free_access(obj):
        """
        Returns days until free(almost free) access to soft-deleted author entry or zero after time has elapsed.
        """
        author = obj.entry_author
        days_until_access = (
                (author.deleted_time + timezone.timedelta(days=constants.DAYS_ELAPSED_SOFT_DELETED_USER))
                - timezone.now()
        ).days
        return max((days_until_access, 0))

    def get_series_name(self, obj):
        """
        Returns name of the correspondent series. Implemented via serializer method as
        we already have series object retrieved in view and do not need to retrieve it again
        directly or via select_related.
        """
        view = self.context['view']
        return view.series.name

    def get_fields(self):
        """
        Discards 'days_until_free_access' field in case:
        a) Author is not soft deleted.
        b) Author deleted_time is None.
        c) Author has alive slaves or master.
        """
        fields = super().get_fields()
        entry_author = self.context['view'].get_object().entry_author

        if not entry_author.deleted or \
                entry_author.deleted_time is None or \
                entry_author.have_slaves_or_master_alive:
            fields.pop('days_until_free_access')

        return fields


class ManagePermissionsSerializer(serializers.ModelSerializer):
    """
    Serializer for managing user object permissions in UserObjectPermissionView.
    """

    class MODEL_CHOICES(TextChoices):
        TVSERIES = archives.models.TvSeriesModel._meta.model_name
        SEASONS = archives.models.SeasonModel._meta.model_name
        IMAGES = archives.models.ImageModel._meta.model_name

    user = serializers.EmailField(
        source='user.email',
    )
    model = serializers.ChoiceField(
        source='content_type.model',
        choices=MODEL_CHOICES.choices,
    )
    object_pk = serializers.IntegerField(
    )

    class Meta:
        model = guardian.models.UserObjectPermission
        exclude = ('content_type', 'permission', )

    def validate_user(self, value):

        permission_giver = self.context['request'].user
        #  Check whether permission receiver exists in fact.
        try:
            permission_receiver = get_user_model().objects.get(email=value)
        except get_user_model().DoesNotExist as err:
            raise serializers.ValidationError(
                *error_codes.USER_DOESNT_EXISTS,
            ) from err

        #  Can't assign to himself.
        if permission_giver == permission_receiver:
            raise serializers.ValidationError(
                *error_codes.PERM_TO_SELF,
            )

        #  Can't assign to master.
        elif permission_giver.master == permission_receiver:
            raise serializers.ValidationError(
                *error_codes.PERM_TO_MASTER,
            )

        #  Can't assign to slave.
        elif permission_giver == permission_receiver.master:
            raise serializers.ValidationError(
                *error_codes.PERM_TO_SLAVE,
            )

        return permission_receiver

    def validate(self, attrs):
        permission_giver = self.context['request'].user
        model_name = attrs['content_type']['model']
        object_pk = attrs['object_pk']

        model = apps.get_model(app_label=__package__, model_name=model_name)
        #  Check whether instance of model does exist.
        try:
            obj = attrs['obj'] = model.objects.get(pk=int(object_pk))
        except model.DoesNotExist as err:
            raise serializers.ValidationError(
                {'object_pk': error_codes.OBJECT_NOT_EXISTS.message},
                error_codes.OBJECT_NOT_EXISTS.code,
            ) from err

        #  Request user can only grant permissions on his own objects.
        if obj.entry_author != permission_giver:
            raise serializers.ValidationError(
                {'user': error_codes.USER_NOT_AUTHOR.message},
                error_codes.USER_NOT_AUTHOR.code,
            )

        return attrs

    def create(self, validated_data):
        permission_code = self.context['view'].permission_code
        user = validated_data['user']['email']
        obj = validated_data['obj']

        return assign_perm(permission_code, user, obj)



