"""Django Models"""

from django.db import models, IntegrityError
from django.utils.crypto import get_random_string


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

    @staticmethod
    def draw_card(game, player=None, color=Card.GREEN, count=1):
        """Draws a random card that has not been used already"""
        if color == Card.GREEN:
            status = CardGamePlayer.MATCHING
        else:
            status = CardGamePlayer.HAND
        draw_again = True
        while draw_again:
            draw_again = False
            used_cards = CardGamePlayer.objects.filter(game=game).values_list('card__id', flat=True)
            cards = Card.objects.exclude(id__in=used_cards).filter(type=color).order_by('?')[:count]
            for card in cards:
                try:
                    CardGamePlayer.objects.create(
                        card=card,
                        game=game,
                        player=player,
                        status=status
                    )
                except IntegrityError as e:
                    draw_again = True  # Try Again

    @staticmethod
    def submit_card(cardgameplayer_pk):
        """Submits a CardGamePlayer to the Judge"""
        cgp = CardGamePlayer.objects.get(pk=cardgameplayer_pk)
        cgp.status = CardGamePlayer.SUBMITTED
        cgp.player.status = Player.SUBMITTED
        cgp.save()
        return cgp

    @staticmethod
    def pick_card(cardgameplayer_pk):
        """Marks a CardGamePlayer as picked by the Judge"""
        cgp = CardGamePlayer.objects.get(pk=cardgameplayer_pk)
        cgp.status = CardGamePlayer.PICKED
        cgp.player.score += 1
        cgp.save()
        Game.replenish_hands(cgp.game.code)
        return cgp

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

    @staticmethod
    def create_game_code():
        # Create a Unique Game Code
        game_code = ""
        not_a_unique_code = True
        while not_a_unique_code:
            game_code = get_random_string(4, allowed_chars='abcdefghijklmnopqrstuvwxyz')
            try:
                Game.objects.create(code=game_code)
                not_a_unique_code = False

            except IntegrityError:
                not_a_unique_code = True
        return game_code

    @staticmethod
    def replenish_hands(game_code):
        """Replenishes the hands of all players in the game"""
        game = Game.objects.get(code=game_code)
        players = game.players.all()
        for player in players:
            hand_card_count = player.cardgameplayer_set.filter(status='hand').count()
            if hand_card_count < 5:
                CardGamePlayer.draw_card(game, player, color='red', count=(5 - hand_card_count))

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

    @staticmethod
    def add_player_to_game(game_code, player_name):
        game = Game.objects.get(code=game_code)
        player = Player.objects.create(name=player_name, game=game)
        CardGamePlayer.draw_card(game, player, 'red', 5)
        if not CardGamePlayer.objects.filter(game=game, status='matching'):
            # draw green card for new player if no one is currently the judge (and make them the judge)
            CardGamePlayer.draw_card(game, player)
            player.status = Player.JUDGE
            player.save()
        return player

    class Meta(object):
        ordering = ['name']
        verbose_name_plural = "players"

    def __str__(self):
        return str(self.name)
