"""
WSGI config for series project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.db.backends.signals import connection_created
from django.dispatch import receiver

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'series.settings')

application = get_wsgi_application()


@receiver(connection_created)
def setup_postgres(connection, **kwargs):
    """
    Drops statement execution after 30 seconds.
    https://hakibenita.com/9-django-tips-for-working-with-databases#custom-functions
    """
    if connection.vendor != 'postgresql':
        return None
    else:
        # Timeout statements after 30 seconds.
        with connection.cursor() as cursor:
            cursor.execute(f"SET statement_timeout TO {settings.DEFAULT_DATABASE_STATEMENT_TIMEOUT};")
