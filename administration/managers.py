from django.db import models
from django.db.models import F
from django.db.models.functions import Now


class IpBlacklistManager(models.Manager):
    """
    IpBlacklist model custom manager.
    """
    pass


class IpBlacklistQueryset(models.QuerySet):
    """
    IpBlacklist custom queryset.
    """
    def only_active(self) -> models.QuerySet:
        """
        Select only 'active' blacklist records, whose stretch is still has not ran out.
        """
        return self.filter(record_time__gt=Now() - F('stretch'))
