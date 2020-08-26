from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.core import exceptions
from django.db import models, transaction
from django.utils import timezone
from django.utils.decorators import classonlymethod
from django.utils.functional import cached_property
from rest_framework.reverse import reverse
from rest_framework_simplejwt import tokens as jwt_tokens
from rest_framework_simplejwt.token_blacklist import models as sjwt_blacklist_models

import users.managers as users_managers
from series import error_codes
from series.helpers.typing import url
from users.helpers import countries, validators as custom_validators
from users.database_functions import IpCount


class User(AbstractUser):
    """
    Custom user model based on AbstractUser model.
    """

    username = None

    master = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        verbose_name='Slave account if not null',
        related_name='slaves',
        on_delete=models.SET_NULL
    )
    email = models.EmailField(
        verbose_name='email address',
        unique=True
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name='first name'
    )
    last_name = models.CharField(
        max_length=150,
        verbose_name='last name'
    )
    user_country = models.CharField(
        max_length=2,
        choices=countries.COUNTRY_ITERATOR,
        null=True,
        blank=True,
        verbose_name='user country of origin',
        validators=[custom_validators.ValidateOverTheRange(container=countries.CODE_ITERATOR)]
    )
    deleted = models.BooleanField(
        default=False,
        verbose_name='Is user account "deleted".'
    )
    deleted_time = models.DateTimeField(
        verbose_name='Time when user got soft-deleted',
        null=True,
        blank=True,
        editable=False,
    )

    USERNAME_FIELD = 'email'
    #  https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#django.contrib.auth.models.CustomUser.REQUIRED_FIELDS
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    custom_manager = users_managers.CustomUserManager.from_queryset(users_managers.UserQueryset)
    all_objects = custom_manager(alive_only=False)
    objects = custom_manager(alive_only=True)

    class Meta:
        index_together = (
            ('first_name', 'last_name',),
        )
        verbose_name = 'user'
        verbose_name_plural = 'users'
        default_manager_name = 'all_objects'
        constraints = [
            # Checks that country code is according the ISO..
            models.CheckConstraint(
                name='country_code_within_list_of_countries_check',
                check=models.Q(user_country__in=countries.CODE_ITERATOR), ),
            #  Doesn't allow master_id fk point on itself.
            models.CheckConstraint(
                name='point_on_itself_check',
                check=~models.Q(master=models.F('pk'))
            ),
            # Doesnt allow to soft-deleted users have slaves of any kind. Fake constraint.for
            # real one in 0015_deleted_user_slaves_constraint.
            models.CheckConstraint(
                name='slaves_of_deleted_user_check',
                check=models.Q(
                    deleted=models.Func(models.F('master_id'), function='users_user_valid_master')
                ))]

    def __str__(self):
        return f'{"SLAVE ACC." if self.master_id is not None else "MASTER ACC."} ' \
               f'pk - {self.pk},' \
               f' full name - {self.get_full_name()},' \
               f' email - {self.email}'

    def clean(self):
        errors = {}
        # Prevent master fc point to itself(master cant be his own master, same for slave).
        if self.master == self:
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.MASTER_OF_SELF, )}
            )
        #  We make sure  that slave cant own slaves(slave acc. can't have it's own slave accounts).
        #  We use 'filter(master__email=self.email)' lookup as model object doesnt have a pk yet
        #  until it created in DB at least.
        if self.master and self.__class__.objects.filter(master__email=self.email).exists():
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.SLAVE_CANT_HAVE_SALVES, )}
            )
        # We make sure that slave's master is not a slave himself.
        if self.master and self.__class__.objects.filter(pk=self.master_id).first().master is not None:
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.MASTER_CANT_BE_SLAVE, )}
            )
        #  We make sure that soft-deleted user can't have slaves, even soft-deleted ones.
        if (self.master is None and self.deleted) and  \
            self.__class__._default_manager.filter(master=self).exists():
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.DELETED_MASTER_SLAVES, )}
            )

        if errors:
            raise exceptions.ValidationError(errors)

    def save(self, fc=True, fake_del=True, *args, **kwargs):
        if fc:
            self.full_clean()
        super().save(*args, **kwargs)

    @transaction.atomic
    def delete(self, soft_del=True, *args, **kwargs):
        if soft_del:
            self.blacklist_tokens()  # Blacklist all refresh tokens.
            self.liberate()  # Deallocate all slaves. Imitation of SET_NULL.
            self.deleted = True  # Soft delete self.
            self.deleted_time = timezone.now()  # Write time of soft-deletion
            self.save(update_fields=('deleted', 'deleted_time',))
            return f'Account {self.email} is deactivated'
        else:
            return super().delete(*args, **kwargs)

    def undelete(self) -> None:
        """
        Undeletes user entry previously being fake-deleted.
        """
        self.deleted = False
        self.deleted_time = None
        return self.save(update_fields=('deleted', 'deleted_time',))

    def blacklist_tokens(self):
        """
        Blacklists all user's refresh tokens.
        """
        outstanding_tokens_pks = sjwt_blacklist_models.OutstandingToken.objects.filter(
            user=self).values_list('pk', flat=True
                                   )
        blacklist_instances = (
            sjwt_blacklist_models.BlacklistedToken(token_id=pk) for pk in outstanding_tokens_pks
        )
        created_instances = sjwt_blacklist_models.BlacklistedToken.objects.bulk_create(
            blacklist_instances,
            ignore_conflicts=True,
        )
        return created_instances

    @cached_property
    def get_absolute_url(self) -> url:
        return reverse(f'{self.__class__.__name__.lower()}-detail', args=(self.pk,))

    @property
    def my_slaves(self) -> Optional[models.QuerySet]:
        """
        Returns queryset of slaves accounts if user have them or None.
        """
        return self.slaves.all() or None

    @property
    def is_slave(self) -> bool:
        """
        Defines whether or not user is slave(this account is slave account).
        """
        return bool(self.master)

    @property
    def have_slaves_or_master_alive(self) -> bool:
        """
        Returns whether or not user has at least one not soft-deleted master or slave account.
        """
        has_master_alive = False if self.master is None else not self.master.deleted

        return has_master_alive or self.slaves.exists()

    def liberate(self) -> Optional[int]:
        """
        Deallocate slaves accounts from a master one.
        """
        all_slaves = self.__class__._default_manager.filter(master=self)
        return all_slaves.update(master=None)

    def get_tokens_for_user(self) -> dict:
        """
        Returns JWT tokens pair for a current user.
        """
        refresh = jwt_tokens.RefreshToken.for_user(self)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    @property
    def is_available_slave(self) -> bool:
        """
        Returns True if user is available for a slave role.
        """
        return self.__class__.objects.get_available_slaves().filter(pk=self.pk).exists()

    @classonlymethod
    def get_fields_names(cls) -> list:
        """
        Returns list of model's fields names.
        """
        return [field.name for field in cls._meta.local_fields]


class UserIP(models.Model):
    """
    Stores user's IP address and datetime when ip was sampled.
    """
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name='user_ip',
    )
    ip = models.GenericIPAddressField(
        verbose_name='User ip  address'
    )
    sample_time = models.DateTimeField(
        auto_now=True,
        verbose_name='Userip sample time'
    )

    class Meta:
        verbose_name = 'Userip address.'
        verbose_name_plural = 'Userip addresses.'
        get_latest_by = ('sample_time',)
        index_together = (
            ('user', 'ip',)
        )
        constraints = [
            # Check that max. quantity of user ips entries is 3.
            models.CheckConstraint(
                name='max_3_ips',
                check=IpCount(models.F('user_id'), models.Value(3)),
            ), ]

    def __str__(self):
        return f'# {self.pk} -- Ip address of user {self.user_id} / {self.user.email}.'

    @transaction.atomic
    def ip_deque(self, ip_num: int = 3) -> None:
        """
        Method keeps only 3 last distinctip address entries.
        """
        cls = type(self)
        # List of user's ips.
        user_ips = cls.objects.filter(user=self.user, ip=self.ip)
        # We update 'sample_time' if pair of (user,ip) is already exists.
        is_updated = user_ips.update(
            sample_time=(self.sample_time or timezone.now())
        )
        # If pair of (user,ip) doesn't exists, we need to save model entry.
        if not is_updated:
            super().save(force_insert=False, force_update=False, using=None, update_fields=None)
        # Keep only 'ip_num' amount of freship entries. Delete all others.
        ips_to_be_deleted = models.Subquery(
            cls.objects.filter(user=self.user).
                order_by('-sample_time')[ip_num:].values_list('pk', flat=True)
        )
        cls.objects.filter(pk__in=ips_to_be_deleted).delete()

    def save(self, fc=True, force_insert=False, force_update=False, using=None, update_fields=None):
        if fc:
            self.full_clean()
        self.ip_deque(ip_num=3)
