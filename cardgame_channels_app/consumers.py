import logging

from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer

from cardgame_channels_app.game_logic import *

LOGGER = logging.getLogger("cardgame_channels_app")


class CreateGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = create_game_code()
        self.message.channel_session['game_code'] = game_code
        multiplexer.send({'action': 'create_game', 'data': {'game_code': game_code}})


class JoinGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = content.get('game_code')
        player = add_player_to_game(game_code, content.get('player_name'))

        Group(game_code, channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this came code, since auto-add only happens on connect
        Group('player_{}'.format(player.pk), channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this player name, since auto-add only happens on connect

        multiplexer.send({'action': 'join_game', 'data': {'game_code': game_code, 'player': get_player_values(player.pk), 'player_cards': get_cards_in_hand_values_list(player.pk), 'green_card': get_matching_card_values(game_code), 'submitted_cards': get_submitted_cards_values_list(game_code), 'all_players_submitted': get_all_players_submitted(game_code), 'judge': get_judge_player_values(game_code)}})
        multiplexer.group_send(game_code, 'player_joined_game', {'data': {'game_code': game_code, 'player': get_player_values(player.pk), 'players': get_game_player_values_list(player.game.code)}})  # notify everyone in the game a player has joined


class PickCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = pick_card(content.get('game_code'), content.get('card_pk'))
        players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
        judge = get_judge_player_values(content.get('game_code'))
        green_card = get_matching_card_values(cgp.game.code)

        # notify everyone card was picked
        multiplexer.group_send(content.get('game_code'), 'pick_card', {'data': {'picked_player': get_player_values(cgp.player.pk), 'card': get_card_values(content.get('game_code'), cgp.card), 'players': players}})

        # Draw new cards and send out to everyone, one by one
        replenish_hands(content.get('game_code'))
        for player in players:
            player_cards = get_cards_in_hand_values_list(player.get('pk'))
            multiplexer.group_send('player_{}'.format(player.get('pk')), 'new_cards', {'data': {'game_code': content.get('game_code'), 'judge': judge, 'green_card': green_card, 'cards': player_cards}})


class SubmitCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = submit_card(content.get('game_code'), content.get('card_pk'))
        multiplexer.group_send('player_{}'.format(cgp.player.pk), 'submit_card', {'data': {'game_code': content.get('game_code'), 'cards': get_cards_in_hand_values_list(cgp.player.pk)}})
        players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
        multiplexer.group_send(content.get('game_code'), 'card_was_submitted', {'data': {'game_code': content.get('game_code'), 'submitting_player': get_player_values(cgp.player.pk), 'players': players, 'card': get_card_values(content.get('game_code'), cgp.card), 'submitted_cards': get_submitted_cards_values_list(cgp.game.code)}})  # notify everyone card was submitted


class GameDemultiplexer(WebsocketDemultiplexer):
    # Looks at the 'stream' value to route the incoming request to the correct consumer
    consumers = {
        "create_game": CreateGameConsumer,
        "join_game": JoinGameConsumer,
        "pick_card": PickCardConsumer,
        "submit_card": SubmitCardConsumer,
    }
