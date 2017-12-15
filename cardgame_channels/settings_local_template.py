"""
Django settings for project.
"""

# pylint: disable=W0614,W0401,W0123,I0011

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

# This file overrides any settings from the main settings file for a docker compose use.

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_PASSWORD = ''
EMAIL_HOST_USER = 'cyfacecardgame@gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
ACCOUNT_EMAIL_VERIFICATION = 'none'

