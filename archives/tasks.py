from __future__ import absolute_import, unicode_literals

from celery import shared_task
from series.helpers import custom_functions


@shared_task
def clean_media_root():
    custom_functions.clean_garbage_in_folder()
