"""
Django settings for project.
"""

# pylint: disable=W0614,W0401,W0123,I0011

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

# This file overrides any settings from the main settings file for a docker compose use.

try:
    from .settings import *
except ImportError:
    pass

DEBUG = False

ADMINS = [('Tim', 'tim@cyface.com'), ]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'database',
        'PORT': 5432,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "asgi_redis.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],
        },
        "ROUTING": "cardgame_channels_app.routing.channel_routing",
    },
}

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'interfaceserver', ]

# Logging
LOGGING = {
    'version': 1,
    "disable_existing_loggers": False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'debug_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'debug.log')
        },
        'error_log': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log')
        },
    },
    'loggers': {
        "root": {
            "handlers": ["console", 'debug_log', 'error_log'],
            'propagate': True,
            "level": "DEBUG",
        },
        'django': {
            'handlers': ['console', 'debug_log', 'error_log'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'django.request': {
            'handlers': ['mail_admins', 'debug_log', 'error_log'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console', 'debug_log', 'error_log'],
            'level': 'INFO',
            'propagate': True,
        },
        'cardgame_channels_app': {
            'handlers': ['console', 'error_log', 'debug_log'],
            'propagate': True,
            'level': 'DEBUG',
        },
    }
}

