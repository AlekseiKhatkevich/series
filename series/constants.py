import datetime


DEFAULT_OBJECT_LEVEL_PERMISSION_CODE = 'permissiveness'
LUMIERE_FIRST_FILM_DATE = datetime.date(1896, 1, 6)
HANDLE_DELETED_USERS_GROUP = 'handle_deleted_users_data'
DAYS_ELAPSED_SOFT_DELETED_USER = 183

TIMEOUTS = {
    'default': 60 * 60,
    'statuslog': 60 * 60,
    'entrieschangelog': 60 * 60,
}

IP_BLACKLIST_CACHE_KEY = 'blacklist'
