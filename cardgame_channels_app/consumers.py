import logging

from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer

from cardgame_channels_app.forms import JoinGameForm, GameCodeForm, GameCodeCardForm, BootPlayerForm
from cardgame_channels_app.game_logic import *

LOGGER = logging.getLogger("cardgame_channels_app")


class BootPlayerConsumer(JsonWebsocketConsumer):
    """Takes a game_code and player_pk and removes that player from the game"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        boot_player_form = BootPlayerForm({'game_code': content.get('game_code'), 'player_pk': content.get('player_pk')})
        if boot_player_form.is_valid():
            try:
                player = Player.objects.get(pk=boot_player_form.cleaned_data.get('player_pk'))
                multiplexer.send({'action': 'boot_player', 'data': {'game_code': boot_player_form.cleaned_data.get('game_code'), 'player_name': player.name, 'players': get_game_player_values_list(player.game.code), 'valid': True}})
                player.delete()
            except ObjectDoesNotExist:
                multiplexer.send({'action': 'boot_player', 'data': {'game_code': boot_player_form.cleaned_data.get('game_code'), 'players': get_game_player_values_list(boot_player_form.cleaned_data.get('game_code')), 'error': 'boot failed', 'errors': boot_player_form.errors, 'valid': False}})


class CreateGameConsumer(JsonWebsocketConsumer):
    """Creates a game and returns it's game_code"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = create_game_code()
        multiplexer.send({'action': 'create_game', 'data': {'game_code': game_code}})


class JoinGameConsumer(JsonWebsocketConsumer):
    """Takes a game_code and a player name and adds that player to the game, and sends them the game data"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        join_form = JoinGameForm({'game_code': content.get('game_code'), 'player_name': content.get('player_name')})
        if join_form.is_valid():
            game_code = join_form.cleaned_data.get('game_code')
            player = add_player_to_game(game_code, join_form.cleaned_data.get('player_name'))

            Group(game_code, channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this came code, since auto-add only happens on connect
            Group('player_{}'.format(player.pk), channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this player name, since auto-add only happens on connect

            multiplexer.send({'action': 'join_game', 'data': {'game_code': game_code, 'player': get_player_values(player.pk), 'player_cards': get_cards_in_hand_values_list(player.pk), 'green_card': get_matching_card_values(game_code), 'submitted_cards': get_submitted_cards_values_list(game_code), 'all_players_submitted': get_all_players_submitted(game_code), 'judge': get_judge_player_values(game_code)}})
            multiplexer.group_send(game_code, 'player_joined_game', {'data': {'game_code': game_code, 'player': get_player_values(player.pk), 'players': get_game_player_values_list(player.game.code)}})  # notify everyone in the game a player has joined
        else:
            multiplexer.send({'action': 'join_game', 'data': {'error': 'join failed', 'errors': join_form.errors}})


class PickCardConsumer(JsonWebsocketConsumer):
    """Takes a game_code and a card_pk and marks that card as picked"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        pick_card_form = GameCodeCardForm(content)
        if pick_card_form.is_valid():
            cgp = pick_card(pick_card_form.cleaned_data.get('game_code'), pick_card_form.cleaned_data.get('card_pk'))
            players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
            judge = get_judge_player_values(cgp.game.code)
            green_card = get_matching_card_values(cgp.game.code)

            # notify everyone card was picked
            multiplexer.group_send(cgp.game.code, 'pick_card', {'data': {'picked_player': get_player_values(cgp.player.pk), 'card': get_card_values(cgp.game.code, cgp.card), 'players': players}})

            # Draw new cards and send out to everyone, one by one
            replenish_hands(cgp.game.code)
            for player in players:
                player_cards = get_cards_in_hand_values_list(player.get('pk'))
                multiplexer.group_send('player_{}'.format(player.get('pk')), 'new_cards', {'data': {'game_code': cgp.game.code, 'judge': judge, 'green_card': green_card, 'cards': player_cards}})
        else:
            multiplexer.send({'action': 'pick_card', 'data': {'error': 'pick card failed', 'errors': pick_card_form.errors}})


class SubmitCardConsumer(JsonWebsocketConsumer):
    """Takes a game code and card_pk and marks that card as submitted"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        submit_card_form = GameCodeCardForm(content)
        if submit_card_form.is_valid():
            cgp = submit_card(submit_card_form.cleaned_data.get('game_code'), submit_card_form.cleaned_data.get('card_pk'))
            multiplexer.group_send('player_{}'.format(cgp.player.pk), 'submit_card', {'data': {'game_code': cgp.game.code, 'cards': get_cards_in_hand_values_list(cgp.player.pk)}})
            players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
            multiplexer.group_send(cgp.game.code, 'card_was_submitted', {'data': {'game_code': cgp.game.code, 'submitting_player': get_player_values(cgp.player.pk), 'players': players, 'card': get_card_values(cgp.game.code, cgp.card), 'submitted_cards': get_submitted_cards_values_list(cgp.game.code), 'all_players_submitted': get_all_players_submitted(cgp.game.code)}})  # notify everyone card was submitted
        else:
            multiplexer.send({'action': 'submit_card', 'data': {'error': 'submit card failed', 'errors': submit_card_form.errors}})


class ValidateGameCodeConsumer(JsonWebsocketConsumer):
    """Takes a game_code and validates that it exists"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code_form = GameCodeForm(content)
        if game_code_form.is_valid():  # Sets cleaned_data we need for send
            multiplexer.send({'action': 'validate_game_code', 'data': {'game_code': game_code_form.cleaned_data.get('game_code'), 'valid': True}})
        else:
            multiplexer.send({'action': 'validate_game_code', 'data': {'game_code': game_code_form.cleaned_data.get('game_code'), 'valid': False, 'errors': game_code_form.errors}})


class ValidatePlayerNameConsumer(JsonWebsocketConsumer):
    """Takes a game_code and player name and validates that it is acceptable and unique to that game"""

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        validate_player_form = JoinGameForm(content)
        if validate_player_form.is_valid():  # Sets cleaned_data we need for send
            multiplexer.send({'action': 'validate_player_name', 'data': {'game_code': validate_player_form.cleaned_data.get('game_code'), 'player_name': validate_player_form.cleaned_data.get('player_name'), 'valid': True}})
        else:
            multiplexer.send({'action': 'validate_player_name', 'data': {'game_code': validate_player_form.cleaned_data.get('game_code'), 'player_name': validate_player_form.cleaned_data.get('player_name'), 'valid': False, 'errors': validate_player_form.errors}})


class GameDemultiplexer(WebsocketDemultiplexer):
    # Looks at the 'stream' value to route the incoming request to the correct consumer

    consumers = {
        "boot_player": BootPlayerConsumer,
        "create_game": CreateGameConsumer,
        "join_game": JoinGameConsumer,
        "pick_card": PickCardConsumer,
        "submit_card": SubmitCardConsumer,
        "validate_game_code": ValidateGameCodeConsumer,
        "validate_player_name": ValidatePlayerNameConsumer,
    }
