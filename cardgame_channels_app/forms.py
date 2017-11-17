"""Django Forms"""

from django.core.exceptions import ObjectDoesNotExist
from django.forms import CharField, Form, HiddenInput, IntegerField, ValidationError
from django.utils.html import strip_tags, escape

from cardgame_channels_app.models import Game, Player


class JoinGameForm(Form):
    """Form to create new games"""
    game_code = CharField(label="Game Code", max_length="4", required=True)
    player_name = CharField(label="Player Name", max_length="10", required=True)

    def clean(self):
        """Since Game Code and Player Name depend on each other, we need to validate them together"""
        cleaned_data = super(JoinGameForm, self).clean()

        # If the data survived the initial cleaning, then check it against the database
        if cleaned_data.get('player_name') and cleaned_data.get('game_code'):
            # Try and make game_code safe
            game_code = escape(strip_tags(cleaned_data['game_code'].lower()))

            # Check if game_code exists
            try:
                Game.objects.get(code=game_code)
                self.cleaned_data['game_code'] = game_code
            except ObjectDoesNotExist:
                self.add_error('game_code', 'Unfortunately, that game code does not exist.')

            # Try and make player_name safe
            player_name = escape(strip_tags(self.cleaned_data['player_name']))

            # Check if player_name is already taken
            try:
                Player.objects.get(game__code=game_code, name=player_name)

                self.add_error('player_name', 'Unfortunately, that player name is already taken.')
            except ObjectDoesNotExist:  # Must be unique if did not exist
                self.cleaned_data['player_name'] = player_name


class GameCodeForm(Form):
    """Form to create new games"""
    game_code = CharField(label="Game Code", max_length="4", required=True)

    def clean_game_code(self):
        game_code = escape(strip_tags(self.cleaned_data['game_code'].lower()))

        # Check if game_code exists
        try:
            Game.objects.get(code=game_code)
        except ObjectDoesNotExist:
            self.add_error('game_code', 'Unfortunately, that game code does not exist.')

        return self.cleaned_data['game_code']


class GameCodeCardForm(Form):
    """Form to when game code and card are submitted together"""
    game_code = CharField(label="Game Code", max_length="4", required=True)
    card_pk = IntegerField(label="Card PK", required=True)

    def clean_game_code(self):
        return escape(strip_tags(self.cleaned_data['game_code']))


class BootPlayerForm(Form):
    """Form to boot disconnected players"""
    game_pk = None
    player_id = IntegerField(label="Player PK", required=True, widget=HiddenInput)
    player = None

    def __init__(self, request, *args, **kwargs):
        super(BootPlayerForm, self).__init__(*args, **kwargs)
        self.game_pk = request.session.get('game_pk', None)

    def clean_player_id(self):
        """Checks to see if the player exists upon form submit"""
        player_id = self.cleaned_data['player_id']

        try:
            self.player = Player.objects.get(pk=player_id, game__id=self.game_pk)
        except ObjectDoesNotExist:
            raise ValidationError("Unfortunately, that player does not exist.")

        return player_id
