from typing import Generic, Iterator, NewType, TypeVar

from django.db import models


User_instance = NewType('User_instance', models.Model)
ip_instance = NewType('ip_instance', models.Model)
jwt_token = NewType('jwt_token', str)
url = NewType('url', str)

_Z = TypeVar("_Z")


class QueryType(Generic[_Z], models.QuerySet):
    """
    Represents django queryset type.
    """
    def __iter__(self) -> Iterator[_Z]: ...
