from typing import Optional

from django.contrib.auth.models import AbstractUser
from django.core import exceptions
from django.db import models
from django.utils.functional import cached_property
from rest_framework.reverse import reverse
from rest_framework_simplejwt import tokens as jwt_tokens

import users.managers as users_managers
from series import error_codes
from users.helpers import countries, validators as custom_validators


class User(AbstractUser):
    """
    Custom user model based on AbstractUser model.
    """

    username = None

    master = models.ForeignKey(
        'self',
        blank=True,
        null=True,
        db_index=False,
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

    USERNAME_FIELD = 'email'
    #  https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#django.contrib.auth.models.CustomUser.REQUIRED_FIELDS
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    objects = users_managers.CustomUserManager.from_queryset(users_managers.UserQueryset)()

    class Meta:
        unique_together = (
            ('first_name', 'last_name',),
        )
        index_together = unique_together
        verbose_name = 'user'
        verbose_name_plural = 'users'
        constraints = [
            models.CheckConstraint(
                name='country_code_within_list_of_countries_check',
                check=models.Q(user_country__in=countries.CODE_ITERATOR),),
            models.CheckConstraint(
                name='point_on_itself_check',
                check=~models.Q(master=models.F('pk'))
            )
        ]

    def __str__(self):
        return f'{"SLAVE ACC." if self.master else "MASTER ACC."} ' \
               f'pk - {self.pk},' \
               f' full name - {self.get_full_name()},' \
               f' email - {self.email}'

    def clean(self):
        errors = {}
        #  We make sure  that slave cant own slaves(slave acc. can't have it's own slave accounts).
        #  We use 'filter(master__email=self.email)' lookup as model object doesnt have a pk yet
        #  until it created in DB at least.
        if self.master and self.__class__.objects.filter(master__email=self.email).exists():
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.SLAVE_CANT_HAVE_SALVES,)}
            )
        # We make sure that slave's master is not a slave himself.
        if self.master and self.__class__.objects.filter(pk=self.master_id).first().master is not None:
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.MASTER_CANT_BE_SLAVE,)}
            )
        # Prevent master fc point to itself(master cant be his own master, same for slave).
        if self.master is self:
            errors.update(
                {'master': exceptions.ValidationError(
                    *error_codes.MASTER_OF_SELF,
                    )}
            )

        if errors:
            raise exceptions.ValidationError(errors)

    def save(self, fc=True, *args, **kwargs):
        if fc:
            self.full_clean()
        super().save(*args, **kwargs)

    @cached_property
    def get_absolute_url(self) -> str:
        return reverse(f'{self.__class__.__name__.lower()}-detail', args=(self.pk, ))

    @property
    def my_slaves(self) -> Optional[models.QuerySet]:
        """
        Returns queryset of slaves accounts if user have them or None.
        """
        return self.__class__.objects.filter(master=self) or None

    @property
    def is_slave(self) -> bool:
        """
        Defines whether or not user is slave( this account is slave account).
        """
        return bool(self.master)

    def get_tokens_for_user(self) -> dict:
        """
        Returns JWT tokens pair for a current user.
        """
        refresh = jwt_tokens.RefreshToken.for_user(self)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


