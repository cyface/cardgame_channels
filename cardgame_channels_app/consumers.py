import logging

from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer

from cardgame_channels_app.models import Game, Player, CardGamePlayer, Card

LOGGER = logging.getLogger("cardgame_channels_app")


def get_connection_groups(game_code):
    LOGGER.debug("CONNECTION GROUPS")
    LOGGER.debug(game_code)
    if game_code and game_code != 'create':
        return [game_code]
    else:
        return []


class CreateGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        game_code = Game.create_game_code()
        self.message.channel_session['game_code'] = game_code
        multiplexer.send({'action': 'create_game', 'data': {'game_code': game_code}})


class JoinGameConsumer(JsonWebsocketConsumer):
    channel_session = True

    # Sets the game code as the group name for all streams
    def connection_groups(self, **kwargs):
        return get_connection_groups(self.kwargs.get('game_code'))

    def receive(self, content, **kwargs):
        LOGGER.debug("RECEIVE GROUPS")
        LOGGER.debug(self.connection_groups())
        multiplexer = kwargs.get('multiplexer')
        player = Player.add_player_to_game(self.kwargs.get('game_code'), content.get('player_name'))
        players = list(player.game.players.values('name', 'score'))
        player_cards = list(player.cardgameplayer_set.filter(card__type=Card.RED).values('pk', 'card__name', 'card__text'))
        green_card = CardGamePlayer.objects.get(game=player.game, status=CardGamePlayer.MATCHING)
        judge_name = 'you' if green_card.player.name == player.name else green_card.player.name
        green_card_values = CardGamePlayer.objects.values('pk', 'card__name', 'card__text').get(game=player.game, status=CardGamePlayer.MATCHING)
        submitted_cards = list(CardGamePlayer.objects.filter(game=player.game, status='submitted').values('pk', 'card__name', 'card__text'))
        multiplexer.send({'action': 'join_game', 'data': {'game': self.kwargs.get('game_code'), 'players': players, 'player_cards': player_cards, 'green_card': green_card_values, 'submitted_cards': submitted_cards, 'judge_name': judge_name}})
        multiplexer.group_send(self.kwargs.get('game_code'), 'player_joined_game', {'data': {'player_name': player.name, 'player_pk': player.pk}})  # notify everyone in the game a player has joined


class SubmitCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    # Sets the game code as the group name for all streams
    def connection_groups(self, **kwargs):
        return get_connection_groups(self.kwargs.get('game_code'))

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = CardGamePlayer.submit_card(content.get('cardgameplayer_pk'))
        multiplexer.group_send(self.kwargs.get('game_code'), 'submit_card', {'data': {'player_pk': cgp.player.pk, 'cardgameplayer_pk': cgp.pk, 'card_name': cgp.card.name, 'card_text': cgp.card.text}})  # notify everyone card was submitted


class GameDemultiplexer(WebsocketDemultiplexer):
    # Looks at the 'stream' value to route the incoming request to the correct consumer
    consumers = {
        "create_game": CreateGameConsumer,
        "join_game": JoinGameConsumer,
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
