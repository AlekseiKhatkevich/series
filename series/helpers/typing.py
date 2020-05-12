from django.db.models import QuerySet
from typing import Iterator, TypeVar, Generic

_Z = TypeVar("_Z")


class QueryType(Generic[_Z], QuerySet):
    """
    Represents django queryset type.
    """
    def __iter__(self) -> Iterator[_Z]: ...
