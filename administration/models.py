from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import BrinIndex, GinIndex
from django.db import models
from django.utils.functional import cached_property
from rest_framework.reverse import reverse

from administration.encoders import CustomEncoder


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
    state = JSONField(
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
