from __future__ import absolute_import, unicode_literals

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import smtplib


@shared_task(
    bind=True,
    autoretry_for=(smtplib.SMTPException,),
    retry_kwargs={
        'max_retries': 5,
        'default_retry_delay': 10 * 6,
    }, )
def send_one_email(self: shared_task, series: dict) -> None:
    """
    Sends one email to list of addresses.
    """
    series_name = series['name']
    imdb_url = series['imdb_url']
    to_emails = series['responsible'].split(',')

    subject = f'Series "{series_name}" entry contains invalid URL to imdb.'
    message = f'You series "{series_name}" entry email to IMDB on web site {settings.SITE_NAME} ' \
              f'contains invalid url {imdb_url}. Please check it and correct or update.' \
              f' Thank you.'

    from_email = settings.ADMINS[0][-1]
    recipient_list = [*to_emails, ]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)

