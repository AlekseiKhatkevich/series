from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.indexes import BrinIndex
from django.db import models


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

    def __str__(self):
        return f'pk = {self.pk}, user pk = {self.user_id}, access_time = {self.access_time}'

    class Meta:

        verbose_name = 'Entries log'
        verbose_name_plural = 'Entries logs'
        get_latest_by = ('access_time', )
        indexes = [
            BrinIndex(fields=('access_time',), autosummarize=True,),
        ]
        constraints = [
            models.CheckConstraint(
                name='as_who_check',
                check=models.Q(as_who__in=UserStatusChoices.values)
            ),
            models.CheckConstraint(
                name='operation_type_check',
                check=models.Q(operation_type__in=OperationTypeChoices.values)
            ), ]
