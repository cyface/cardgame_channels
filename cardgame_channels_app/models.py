"""Django Models"""

from django.db import models


class Card(models.Model):
    """Card for cardgame"""

    # Card Colors
    GREEN = 'green'
    RED = 'red'

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, blank=True, null=True)
    text = models.TextField(blank=True, null=True)
    players = models.ManyToManyField('Player', through='CardGamePlayer')
    games = models.ManyToManyField('Game', through='CardGamePlayer')
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ['name']
        verbose_name_plural = "cards"

    def __str__(self):
        return str(self.name)


class CardGamePlayer(models.Model):
    """Card-Game-Player assignment for cardgame"""

    # CardGamePlayer Status Values
    HAND = 'hand'  # In the player's hand
    SUBMITTED = 'submitted'  # Submitted as choice to the chooser
    PICKED = 'picked'  # Chosen as the winner by the chooser
    MATCHING = 'matching'  # Actively being matched by the players
    WON = 'won'  # won as the prize by being picked by the chooser
    LOST = 'lost'  # not picked by the chooser

    status = models.CharField(max_length=30, default='hand', db_index=True)
    card = models.ForeignKey('Card')
    game = models.ForeignKey('Game')
    player = models.ForeignKey('Player')

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ['date_created']
        unique_together = (('card', 'game'),)
        verbose_name_plural = "Card Game Players"
        verbose_name = "Card Game Player"

    def __str__(self):
        return str(self.game.code + ":" + self.card.name + ":" + self.status)


class Game(models.Model):
    """Game for cardgame"""

    code = models.CharField(max_length=255, unique=True, db_index=True)
    cards = models.ManyToManyField('Card', through='CardGamePlayer')
    # players available as players

    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ['code']
        verbose_name_plural = "games"

    def __str__(self):
        return str(self.code)


class Player(models.Model):
    """Player for cardgame."""

    # Player Status Values
    WAITING = 'waiting'  # Waiting for Player to Submit
    SUBMITTED = 'submitted'  # Player Has Submitted a Card
    JUDGE = 'judge'  # Player is the Judge for This Round

    name = models.CharField(max_length=20)
    game = models.ForeignKey('cardgame_channels_app.Game', blank=True, null=True, related_name='players')
    cards = models.ManyToManyField('Card', through=CardGamePlayer)
    status = models.CharField(max_length=20, default='waiting')  # waiting, submitted, judge
    score = models.IntegerField(default=0)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ['name']
        verbose_name_plural = "players"

    def __str__(self):
        return str(self.name)
