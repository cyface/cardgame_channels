import logging

from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer

from cardgame_channels_app.models import Game, Player, CardGamePlayer, Card

LOGGER = logging.getLogger("cardgame_channels_app")


class CreateGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = Game.create_game_code()
        self.message.channel_session['game_code'] = game_code
        multiplexer.send({'action': 'create_game', 'data': {'game_code': game_code}})


class JoinGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = content.get('game_code')
        Group(game_code, channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this came code, since auto-add only happens on connect
        player = Player.add_player_to_game(game_code, content.get('player_name'))
        players = list(player.game.players.values('name', 'score'))
        player_cards = list(player.cardgameplayer_set.filter(card__type=Card.RED).values('pk', 'card__name', 'card__text'))
        green_card = CardGamePlayer.objects.get(game=player.game, status=CardGamePlayer.MATCHING)
        judge_name = 'you' if green_card.player.name == player.name else green_card.player.name
        green_card_values = CardGamePlayer.objects.values('pk', 'card__name', 'card__text').get(game=player.game, status=CardGamePlayer.MATCHING)
        submitted_cards = list(CardGamePlayer.objects.filter(game=player.game, status='submitted').values('pk', 'card__name', 'card__text'))
        multiplexer.send({'action': 'join_game', 'data': {'game_code': game_code, 'players': players, 'player_cards': player_cards, 'green_card': green_card_values, 'submitted_cards': submitted_cards, 'judge_name': judge_name}})
        multiplexer.group_send(game_code, 'player_joined_game', {'data': {'game_code': game_code, 'player_name': player.name, 'player_pk': player.pk}})  # notify everyone in the game a player has joined


class PickCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = CardGamePlayer.pick_card(content.get('cardgameplayer_pk'))
        # TODO: Send players out their new cards.  Send out updated score
        multiplexer.group_send(content.get('game_code'), 'pick_card', {'data': {'player_pk': cgp.player.pk, 'player_name': cgp.player.name, 'cardgameplayer_pk': cgp.pk, 'card_name': cgp.card.name, 'card_text': cgp.card.text}})  # notify everyone card was submitted


class SubmitCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = CardGamePlayer.submit_card(content.get('cardgameplayer_pk'))
        multiplexer.group_send(content.get('game_code'), 'submit_card', {'data': {'player_pk': cgp.player.pk, 'player_name': cgp.player.name, 'cardgameplayer_pk': cgp.pk, 'card_name': cgp.card.name, 'card_text': cgp.card.text}})  # notify everyone card was submitted


class GameDemultiplexer(WebsocketDemultiplexer):
    # Looks at the 'stream' value to route the incoming request to the correct consumer
    consumers = {
        "create_game": CreateGameConsumer,
        "join_game": JoinGameConsumer,
        "pick_card": PickCardConsumer,
        "submit_card": SubmitCardConsumer,
    }




















    # # noinspection
    # # PyProtectedMember, PyBroadException, PyUnusedLocal, PyUnusedLocal
    # @receiver([post_delete, post_save], sender=CardGamePlayer)
    # def update_cards(sender, instance, **kwargs):
    #     """
    #     Updates the player/card data when a Card is changed.
    #     Django prevents this from triggering from the admin until 1.9
    #     """
    #     # Increment the player's score if their card just won
    #     if instance.status == 'picked':
    #         try:
    #             instance.player.score += 1
    #             instance.player.save()
    #             won_card = CardGamePlayer.objects.get(game=instance.game, status='matching')
    #             won_card.status = 'won'
    #             won_card.player = instance.player
    #             won_card.save()
    #             lost_cards = CardGamePlayer.objects.filter(game=instance.game, status='submitted').update(status='lost')
    #             print(lost_cards)
    #             CardGamePlayer.replenish_hands(instance.game)
    #             CardGamePlayer.draw_card(game=instance.game, player=instance.player)  # New Green Card to Picked Player
    #         except Exception as e:
    #             print(e)
    #
    #     # Try updating the current game attached to this cardgameplayer
    #     try:
    #         instance.game._publish('updated', changed_fields=['players', 'cardgameplayer_set'])
    #     except:
    #         pass
    #
    #
    # # noinspection
    # # PyProtectedMember, PyBroadException, PyUnusedLocal, PyUnusedLocal
    # @receiver([post_save, post_delete], sender=Player)
    # def update_players(sender, instance, **kwargs):
    #     """Updates the player/game data when a Player is changed"""
    #
    #     # Try updating the current game attached to this player
    #     try:
    #         instance.game._publish('updated', changed_fields=['players', 'cardgameplayer_set'])
    #     except:
    #         pass
    #
    #     # Try updating the previous game attached to this player
    #     try:
    #         previous_game = Game.objects.get(pk=instance._pre_save_state.get('game_id'))
    #         previous_game._publish('updated', changed_fields=['players'])
    #     except:
    #         pass
