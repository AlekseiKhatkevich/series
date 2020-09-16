# Celery related settings.
from celery.schedules import crontab
from django.conf import settings

REDIS_HOST = settings.REDIS_HOST
REDIS_PORT = settings.REDIS_PORT
broker_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'
broker_transport_options = {'visibility_timeout': 3600}
result_backend = f'redis://{REDIS_HOST}:{REDIS_PORT}/1'

accept_content = ['json', 'pickle']
task_serializer = 'pickle'
result_serializer = 'pickle'

timezone = 'Europe/Moscow'

beat_schedule = {
    'delete stale tokens': {
        'task': 'users.tasks.clean_stale_tokens',
        'schedule': crontab(hour=17, minute=00),
    },
    'clean_media_root': {
        'task': 'archives.tasks.clean_media_root',
        'schedule': crontab(hour=17, minute=1, day_of_week='sat'),
    },
    'clean_stale_permissions': {
        'task': 'users.tasks.clean_stale_permissions',
        'schedule': crontab(hour=17, minute=2),
    },
    'notify_users': {
        'task': 'archives.tasks.notify_authors_about_invalid_urls',
        'schedule': crontab(hour=17, minute=3),
    },
    'delete_old_logs': {
        'task': 'administration.tasks.clear_old_logs',
        'schedule': crontab(hour=17, minute=4, day_of_week='sat'),
        'args': (10000, )
    },
    'delete_old_ip_blacklist_entries': {
        'task': 'administration.tasks.delete_non_active_blacklisted_ips',
        'schedule': crontab(hour=17, minute=5),
    }
}

