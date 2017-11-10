"""Django Forms"""

from django.forms import CharField, Form, HiddenInput, IntegerField, ValidationError
from cardgame_channels_app.models import Game, Player
from django.core.exceptions import ObjectDoesNotExist


class JoinGameForm(Form):
    """Form to create new games"""
    game_code = CharField(label="Game Code", max_length="6", required=True)
    player_name = CharField(label="Player Name", max_length="10", required=True)
    game = None

    def clean_game_code(self):
        """Makes the input game code lower case"""
        game_code = self.cleaned_data['game_code'].lower()

        try:
            self.game = Game.objects.get(code=game_code)
        except ObjectDoesNotExist:
            raise ValidationError("Unfortunately, that game code is not valid.")

        return game_code


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
