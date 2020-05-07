from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core import exceptions

from rest_framework.reverse import reverse

import users.managers as users_managers
from users.helpers import countries, validators as custom_validators

from rest_framework_simplejwt import tokens as jwt_tokens


class User(AbstractUser):
    """
    Custom user model based on AbstractUser model.
    """

    username = None

    master = models.ForeignKey(
        'self',
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
        verbose_name='user country of origin',
        validators=[custom_validators.ValidateOverTheRange(container=countries.CODE_ITERATOR)]
    )

    USERNAME_FIELD = 'email'
    #  https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#django.contrib.auth.models.CustomUser.REQUIRED_FIELDS
    REQUIRED_FIELDS = ['first_name', 'last_name', ]

    objects = users_managers.CustomUserManager()

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
        ]

    def __str__(self):
        return f'{"SLAVE ACC." if self.master else "MASTER ACC."} ' \
               f'pk - {self.pk},' \
               f' full name - {self.get_full_name()},' \
               f' email - {self.email}'

    def clean(self):
        errors = {}
        #  We make sure  that slave cant own slaves(slave acc. can't have it's own slave accounts).
        if self.master and self.__class__.objects.filter(master=self).exists():
            errors.update(
                {'master': exceptions.ValidationError(
                    "Slave account can't have its own slaves",
                    code='slave_cant_have_salves'), }
            )
        # We make sure that slave's master is not a slave himself.
        elif self.master and self.__class__.objects.filter(pk=self.master_id).first().master is not None:
            errors.update(
                {'master': exceptions.ValidationError(
                    "This slaves's master can not be slave itself",
                    code='master_cant_be_slave')}
            )
        if errors:
            raise exceptions.ValidationError(errors)

    @property
    def get_absolute_url(self):
        return reverse('user-me')

    @property
    def my_slaves(self):
        """
        Returns queryset of slaves accounts if user have them.
        """
        return self.__class__.objects.filter(master=self)

    def get_tokens_for_user(self):
        """
        Returns JWT tokens pair for a current user.
        """
        refresh = jwt_tokens.RefreshToken.for_user(self)

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


