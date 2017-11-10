"""
Django settings for project.
"""

# pylint: disable=W0614,W0401,W0123

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

# This file overrides any settings from the main settings file for a docker compose use.

try:
    from .settings import *
except ImportError:
    pass

DEBUG = False

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
