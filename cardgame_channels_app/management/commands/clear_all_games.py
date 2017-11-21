"""Removes all Games"""

from django.core.management.base import BaseCommand
from cardgame_channels_app.models import Game


class Command(BaseCommand):
    """
        Removes all games
    """
    help = "Removes all Games"

    def handle(self, **options):
        """Removes all games"""
        Game.objects.all().delete()

        self.stdout.write('Complete\n')
