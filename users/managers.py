from typing import Any, Optional

from django.contrib.auth.base_user import BaseUserManager
from django.core import exceptions
from django.db import models
from django.db.models import Exists, OuterRef, functions

from series import error_codes
from series.helpers import project_decorators
from series.helpers.typing import User_instance


@project_decorators.typeassert(alive_only=bool)
class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of username.
    """

    def __init__(self, *args, **kwargs):
        self.alive_only = kwargs.pop('alive_only', True)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if self.alive_only:
            return qs.exclude(deleted=True)
        return qs

    def create_user(self, email: str, password: str, db_save: bool = True, **extra_fields: Any) -> User_instance:
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

    def create_superuser(self, email: str, password: str, **extra_fields: Any) -> User_instance:
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

    def check_user_and_password(
            self, email: str,
            password: str,
            include_non_active: bool = True,
            include_soft_deleted: bool = False,
    ) -> Optional[User_instance]:
        """
        Validation whether user is exists and if so , whether his(hers) password is correct.
        :include_non_active - If True, search as well among users with 'is_active' is set to False.
        :include_soft_deleted -if True -soft-deleted user will be included in search scope.
        (i.e among all users).
        :returns User instance or None.
        """
        kwargs = {'email': email} if include_non_active else {'email': email, 'is_active': True}
        manager = self.model.objects if not include_soft_deleted else self.model._default_manager

        try:
            user = manager.get(**kwargs)
        except self.model.DoesNotExist as err:
            raise exceptions.ValidationError(
                {'user_email': error_codes.USER_DOESNT_EXISTS.message},
                code=error_codes.USER_DOESNT_EXISTS.code,
            ) from err
        else:
            if not user.check_password(password):
                raise exceptions.ValidationError(
                    {'user_password': f'Incorrect password for user with email - {email}'},
                    code='invalid_password',
                )

            return user

    def is_soft_deleted(self, **kwargs: Any) -> bool:
        """
        Checks whether or not user with given unique data is soft-deleted.
        """
        assert kwargs, 'Provide at least one lookup field (pk, email, etc)'
        return self.model._default_manager.filter(**kwargs, deleted=True).exists()


class UserQueryset(models.QuerySet):
    """
    User model custom queryset.
    """
    def delete(self, soft_del=True):
        if soft_del:
            return self.update(deleted=True, deleted_time=functions.Now())
        else:
            return super().delete()

    def undelete(self) -> int:
        """
        Undeletes previously fake-deleted user entries.
        """
        return self.update(deleted=False, deleted_time=None)

    def get_available_slaves(self) -> models.QuerySet:
        """
        Method returns queryset of all available slaves
        (who doesnt have a master and who isn't a master himself).
        """
        #  https://docs.djangoproject.com/en/3.0/ref/models/expressions/#filtering-on-a-subquery-or-exists-expressions
        has_slaves = Exists(self.filter(master_id=OuterRef('pk')))
        queryset_of_available_slaves = self.filter(master__isnull=True).exclude(has_slaves)
        return queryset_of_available_slaves

    delete.queryset_only = True
    undelete.queryset_only = True


