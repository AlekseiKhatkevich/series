from __future__ import absolute_import, unicode_literals

from celery import shared_task

from administration import custom_functions


@shared_task
def clean_media_root():
    custom_functions.HandleWrongUrls()()
