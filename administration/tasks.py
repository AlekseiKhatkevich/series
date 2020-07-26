from __future__ import absolute_import, unicode_literals

import smtplib

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Min
from django_db_logger.models import StatusLog


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
    responsible_user = series['responsible']
    admin_email = settings.ADMINS[0][-1]

    if responsible_user is None:
        to_emails = [admin_email, ]
    else:
        to_emails = series['responsible'].split(',')

    subject = f'Series "{series_name}" entry contains invalid URL to imdb.'
    message = f'You series "{series_name}" entry email to IMDB on web site {settings.SITE_NAME} ' \
              f'contains invalid url {imdb_url}. Please check it and correct or update.' \
              f' Thank you.'

    from_email = admin_email
    recipient_list = [*to_emails, ]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


@shared_task
def clear_old_logs(keep_num: int) -> tuple:
    """
    Deletes part of the logs exceeded specified quantity.
    For example if we have 20000 logs entries and keep_num = 17000, than oldest 3000
    logs will be deleted.
    """
    threshold_dt = StatusLog.objects.all().order_by('-create_datetime')[: keep_num].\
        aggregate(min_dt=Min('create_datetime'))['min_dt']

    return StatusLog.objects.filter(create_datetime__lt=threshold_dt).delete()
