import logging

from django.conf import settings
from django.core.mail import send_mail
from django.views.generic import TemplateView

LOGGER = logging.getLogger("cardgame_channels_app")


class HomePage(TemplateView):
    """Display Home Page"""
    template_name = 'cardgame/home.html'

