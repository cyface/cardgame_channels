import logging

from django.views.generic import TemplateView

LOGGER = logging.getLogger("cardgame_channels_app")


class HomePage(TemplateView):
    """Display Home Page"""
    template_name = 'cardgame/home.html'

