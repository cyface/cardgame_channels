"""
ASGI config for project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://channels.readthedocs.io/en/stable/deploying.html
"""

# pylint: disable=C0103,E0401

import os

from channels.asgi import get_channel_layer

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cardgame_channels.settings")

channel_layer = get_channel_layer()
