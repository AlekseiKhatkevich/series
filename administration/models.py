from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import BrinIndex, GinIndex
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework.reverse import reverse
import administration.managers

from administration.encoders import CustomEncoder
from administration.helpers import validators as admin_validators
from series import error_codes


class UserStatusChoices(models.TextChoices):
    CREATOR = 'CREATOR'
    SLAVE = 'SLAVE'
    MASTER = 'MASTER'
    FRIEND = 'FRIEND'
    ADMIN = 'ADMIN'
    LEGACY = 'LEGACY'


class OperationTypeChoices(models.TextChoices):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


class EntriesChangeLog(models.Model):
    """
    Keeps information about by whom changes being made in series and seasons.
    """
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    object_id = models.PositiveIntegerField(
    )
    content_object = GenericForeignKey(
        'content_type',
        'object_id',
    )
    user = models.ForeignKey(
        get_user_model(),
        verbose_name='user',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='access_logs',
    )
    access_time = models.DateTimeField(
        verbose_name='access_time',
        auto_now_add=True,
    )
    as_who = models.CharField(
        verbose_name='Status of the accessed user.',
        choices=UserStatusChoices.choices,
        max_length=7,
    )
    operation_type = models.CharField(
        verbose_name='Type of the access operation.',
        choices=OperationTypeChoices.choices,
        max_length=6,
    )
    state = models.JSONField(
        verbose_name='Model state before save or delete.',
        encoder=CustomEncoder,
    )

    class Meta:
        verbose_name = 'Entries log'
        verbose_name_plural = 'Entries logs'
        get_latest_by = ('access_time',)
        indexes = [
            BrinIndex(fields=('access_time',), autosummarize=True, ),
            GinIndex(fields=('state',)),
        ]
        constraints = [
            #  'as_who' might be only one of the options from UserStatusChoices.
            models.CheckConstraint(
                name='as_who_check',
                check=models.Q(as_who__in=UserStatusChoices.values)
            ),
            #  'operation_type' might be only one of the options from OperationTypeChoices.
            models.CheckConstraint(
                name='operation_type_check',
                check=models.Q(operation_type__in=OperationTypeChoices.values)
            ),
            #  One model entry can have only one 'DELETE' or only one 'CREATE'.
            models.constraints.UniqueConstraint(
                name='multiple_delete_or_update_exclusion',
                fields=('object_id', 'operation_type', 'content_type_id'),
                condition=models.Q(
                    operation_type__in=(
                        OperationTypeChoices.DELETE,
                        OperationTypeChoices.CREATE,
                    )), )]

    def save(self, fc=True, *args, **kwargs):
        if fc:
            self.full_clean(validate_unique=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'pk = {self.pk}, object = {self.object_id}, operation_type = {self.operation_type}'

    @cached_property
    def get_absolute_url(self):
        return reverse(
            'history-detail',
            args=((
                self.content_object.__class__._meta.model_name,
                self.object_id,
                self.pk,
            )))


class IpAndNetworkField(models.GenericIPAddressField):
    """

    """

    def __init__(self, verbose_name=None, name=None, protocol='both', unpack_ipv4=False, *args, **kwargs):
        super().__init__(verbose_name, name, protocol, unpack_ipv4, *args, **kwargs)
        self.default_validators = []


class IpBlacklist(models.Model):
    """
    Holds list of blacklisted ips.
    """
    queryset = administration.managers.IpBlacklistQueryset
    objects = administration.managers.IpBlacklistManager.from_queryset(queryset)()

    ip = IpAndNetworkField(
        verbose_name='Ip address.',
        db_index=True,
        primary_key=True,
        unpack_ipv4=True,
        validators=[admin_validators.ValidateIpAddressOrNetwork(24),]
    )
    record_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Ip record time.'
    )
    stretch = models.DurationField(
        verbose_name='Time interval during which ip is blacklisted.',
        validators=[
            validators.MinValueValidator(
                limit_value=timezone.timedelta(microseconds=0),
                message=error_codes.STRETCH_NOT_NEGATIVE.message,
            ), ])

    class Meta:
        verbose_name = 'Ip blacklist.'
        verbose_name_plural = 'Ip blacklists.'
        get_latest_by = ('record_time',)
        index_together = ('record_time', 'stretch', )
        constraints = [
            #  Stretch should be > 0.
            models.CheckConstraint(
                name='stretch_positive_check',
                check=models.Q(stretch__gt=timezone.timedelta(microseconds=0))
            ), ]

    def __str__(self):
        return self.ip

    @property
    def is_active(self):
        """
        Returns True if ip is still blacklisted.
        """
        return (self.record_time + self.stretch) > timezone.now()

    def save(self, fc=True, *args, **kwargs):
        if fc:
            self.full_clean(validate_unique=True)
        super().save(*args, **kwargs)
