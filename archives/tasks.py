from __future__ import absolute_import, unicode_literals

from celery import shared_task
from series.helpers import custom_functions
import administration.handle_urls


@shared_task
def clean_media_root():
    """
    Cleans MEDIA_ROOT from garbage.
    """
    custom_functions.clean_garbage_in_folder()


@shared_task
def notify_authors_about_invalid_urls():
    """
    Send to responsible users information about their series have invalid urls.
    """
    administration.handle_urls.HandleWrongUrls()()
