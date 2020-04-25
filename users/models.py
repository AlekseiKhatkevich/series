from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

import users.managers as users_managers
from .helpers import countries


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
        null=True,
        blank=False,
        max_length=30,
        verbose_name='first name'
    )
    last_name = models.CharField(
        null=True,
        blank=False,
        max_length=150,
        verbose_name='last name'
    )
    user_country = models.CharField(
        max_length=2,
        choices=countries.COUNTRY_ITERATOR,
        null=True,
        verbose_name='user country of origin'
    )

    USERNAME_FIELD = 'email'
    #  https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#django.contrib.auth.models.CustomUser.REQUIRED_FIELDS
    REQUIRED_FIELDS = []

    objects = users_managers.CustomUserManager()

    class Meta:
        unique_together = (
             ('first_name', 'last_name', ),
         )
        index_together = unique_together
        verbose_name = 'user'
        verbose_name_plural = 'users'

    def __str__(self):
        return f'{"SLAVE ACC." if self.master else "MASTER ACC." } ' \
               f'pk - {self.pk},' \
               f' full name - {self.get_full_name()},' \
               f' email - {self.email}'

    # todo
    @property
    def get_absolute_url(self):
        pass

    @property
    def my_slaves(self):
        return self.__class__.objects.filter(master=self)



