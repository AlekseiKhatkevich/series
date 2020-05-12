from typing import Any

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.db.models import Exists, OuterRef

from series.helpers.typing import QuerySet


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of username.
    """

    def create_user(self, email: str, password: str, db_save: bool = True, **extra_fields: Any):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError('Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        if db_save:
            user.save()
        return user

    def create_superuser(self, email: str, password: str, **extra_fields: Any):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields = dict(extra_fields)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        return self.create_user(email, password, **extra_fields)


class UserQueryset(models.QuerySet):
    """
    User model custom queryset.
    """
    def get_available_slaves(self) -> QuerySet:
        """
        Method returns queryset of all available slaves
        (who doesnt have a master and who isn't a master himself).
        """
        #  https://docs.djangoproject.com/en/3.0/ref/models/expressions/#filtering-on-a-subquery-or-exists-expressions
        has_slaves = Exists(self.filter(master_id=OuterRef('pk')))
        queryset_of_available_slaves = self.filter(master__isnull=True).exclude(has_slaves)
        return queryset_of_available_slaves

