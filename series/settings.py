"""Series project root settings."""

import os
from datetime import timedelta

from dotenv import load_dotenv

# .env related settings
load_dotenv()

#  Turns to True when in test mode. Source code are in custom test runner.
IM_IN_TEST_MODE = False

SITE_NAME = 'Series notebook'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', ]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    # project apps
    'archives.apps.ArchivesConfig',
    'users.apps.UsersConfig',

    # 3-rd party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'djoser',
    'drf_yasg',
    'debug_toolbar',
    'corsheaders',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # new
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # new
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'series.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'series.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': 'series_db'},
    'test_test': {  # Test database
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': 'localhost',
        'USER': 'postgres',
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'NAME': 'testdb',
        'TEST': {
            'NAME': 'auto_tests', }
    },
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

MEDIA_ROOT = 'media/'

# https://docs.djangoproject.com/en/3.0/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project

AUTH_USER_MODEL = 'users.User'

#  for Django Debug toolbar
INTERNAL_IPS = ['127.0.0.1', ]

DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
    'debug_toolbar.panels.profiling.ProfilingPanel',
]

#  custom test runner
TEST_RUNNER = 'series.helpers.testrunner.MyTestSuiteRunner'

#  DRF related options.
REST_FRAMEWORK = {
    # 'DEFAULT_AUTHENTICATION_CLASSES': (
    #     'rest_framework_simplejwt.authentication.JWTAuthentication',
    # ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        'series.permissions.SoftDeletedUsersDenied',
    ],
    'EXCEPTION_HANDLER': 'series.helpers.exception_handler.custom_exception_handler',
    'COMPACT_JSON': False,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '60/minute',
        'user': '1000/minute',
        'resend_activation': '1/minute',
        'undelete_account': '1/minute',
    }
}

#  djangorestframework_simplejwt related settings.
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
    'AUTH_HEADER_TYPES': ('Bearer', 'JWT'),
    'ALGORITHM': 'HS512',
    'SIGNING_KEY': os.getenv('JWT_SIGNING_KEY'),
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
    ),
}

#  Djoser related settings.
DJOSER = {
    'TOKEN_MODEL': None,
    'HIDE_USERS': True,
    'SEND_ACTIVATION_EMAIL': False,
    'ACTIVATION_URL': 'example_frontend_url/{uid}/{token}',
    'SLAVE_ACTIVATION_URL': 'example_frontend_url/{master_uid}/{slave_uid}/{token}',
    'EMAIL': {
        'slave_activation': 'users.email.email_classes.SlaveActivationEmail',
    },
    'SERIALIZERS': {
        'user_create': 'users.serializers.CustomDjoserUserCreateSerializer',
        'user': 'users.serializers.CustomUserSerializer',
        'current_user': 'users.serializers.CustomUserSerializer',
        'set_slaves': 'users.serializers.SetSlavesSerializer',
        'undelete_account': 'users.serializers.UndeleteUserAccountSerializer',
    },
    'PERMISSIONS': {
        'set_slaves': ['djoser.permissions.CurrentUserOrAdmin'],
        'password_reset': ['users.permissions.UserIPPermission'],
        'undelete_account': ['rest_framework.permissions.AllowAny'],
        },
}
#  Email related settings.
if IM_IN_TEST_MODE:  # Switch to locmem email backend during tests.
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
