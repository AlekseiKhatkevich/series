from __future__ import absolute_import, unicode_literals

from celery import shared_task
from rest_framework_simplejwt.token_blacklist.management.commands import flushexpiredtokens


@shared_task
def clean_stale_tokens() -> None:
    """
    Flushes any expired tokens in the outstanding token list.
    """
    flushexpiredtokens.Command().handle()


@shared_task
def add(x, y):
    return x + y


@shared_task
def mul(x, y):
    return x * y




