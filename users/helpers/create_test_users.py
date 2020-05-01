from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from typing import Sequence


def create_random_password() -> str:
    """
    Generates random DJANGO ready hashed password.
    """
    return make_password(
        get_user_model().objects.make_random_password()
    )

#  Initial users data.


users_data = {
        'superuser@inbox.ru': {
            'master': None,
            'first_name': 'Super',
            'last_name': 'user',
            'user_country': 'RU',
            'password': create_random_password(),
            'is_superuser': True,
            'is_staff': True,
            'is_active': True,
        },
        'user_1@inbox.ru': {
            'master': None,
            'first_name': 'user_1',
            'last_name': 'Smith',
            'user_country': 'RW',
            'password': create_random_password(),
            'is_superuser': False,
            'is_staff': False,
            'is_active': True,
        },
        'user_2@inbox.ru': {
            'master': None,
            'first_name': 'user_2',
            'last_name': 'Villiams',
            'user_country': 'JP',
            'password': create_random_password(),
            'is_superuser': False,
            'is_staff': False,
            'is_active': True,
        },
    }


def create_users() -> Sequence:
    """
     Creates users in database.
     returns container of user's instances.
    """

    users = get_user_model().objects.bulk_create(
        [get_user_model()(email=email, **fields) for email, fields in users_data.items()]
    )
    return users


def delete_users() -> None:
    """
    Deletes test users from database.
    """
    get_user_model().objects.filter(email__in=users_data.keys()).delete()
