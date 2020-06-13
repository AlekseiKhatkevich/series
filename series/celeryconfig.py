# Celery related settings.
from celery.schedules import crontab


REDIS_HOST = 'localhost'
REDIS_PORT = '6379'
broker_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
broker_transport_options = {'visibility_timeout': 3600}
result_backend = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'

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
    }
}
