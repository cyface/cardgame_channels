"""Admin site customizations for cardgame"""

# pylint: disable=C0111,E0602,F0401,R0904,E1002

from django.contrib import admin
from cardgame_channels_app.models import Card, CardGamePlayer, Game, Player


class CardGamePlayerInline(admin.StackedInline):
    """Inline for CardGamePlayer"""
    model = CardGamePlayer


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    """Admin Setup for Card"""
    date_hierarchy = 'date_created'
    list_display = ['name', 'type']
    inlines = [CardGamePlayerInline, ]


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    """Admin Setup for Player"""
    date_hierarchy = 'date_created'
    inlines = [CardGamePlayerInline, ]


class PlayerInline(admin.StackedInline):
    """Inline Setup for Player"""
    model = Player


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Admin Setup for Game"""
    date_hierarchy = 'date_created'
    inlines = [CardGamePlayerInline, PlayerInline]
