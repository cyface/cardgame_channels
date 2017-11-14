import logging

from channels import Group
from channels.generic.websockets import WebsocketDemultiplexer, JsonWebsocketConsumer

from cardgame_channels_app.models import Game, Player, CardGamePlayer, Card

LOGGER = logging.getLogger("cardgame_channels_app")


def rename_card_fields(card):
    """Renames a card to remove card__ from the field names."""
    return {'pk': card.get('pk'),
            'name': card.get('card__name'),
            'text': card.get('card__text')}


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
        Group('player_{}'.format(player.pk), channel_layer=multiplexer.reply_channel.channel_layer).add(multiplexer.reply_channel)  # Add joiner to group for this player name, since auto-add only happens on connect
        players = list(player.game.players.values('pk', 'name', 'status', 'score'))
        player_cards = Player.get_cards_in_hand_values_list(player.pk)
        green_card = CardGamePlayer.objects.get(game=player.game, status=CardGamePlayer.MATCHING)
        judge_name = 'you' if green_card.player.name == player.name else green_card.player.name
        green_card_values = rename_card_fields(CardGamePlayer.objects.values('pk', 'card__name', 'card__text').get(game=player.game, status=CardGamePlayer.MATCHING))
        submitted_cards = Game.get_submitted_cards_values_list(game_code)
        all_players_submitted = True if 0 < len(submitted_cards) == (len(players) - 1) else False
        multiplexer.send({'action': 'join_game', 'data': {'game_code': game_code, 'player_pk': player.pk, 'player_name': player.name, 'players': players, 'player_cards': player_cards, 'green_card': green_card_values, 'submitted_cards': submitted_cards, 'all_players_submitted': all_players_submitted, 'judge_name': judge_name}})
        multiplexer.group_send(game_code, 'player_joined_game', {'data': {'game_code': game_code, 'player_pk': player.pk, 'player_name': player.name, 'player_score': player.score, 'player_status': player.status, 'players': players}})  # notify everyone in the game a player has joined


class PickCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = CardGamePlayer.pick_card(content.get('cardgameplayer_pk'))
        players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
        multiplexer.group_send(content.get('game_code'), 'pick_card', {'data': {'player_pk': cgp.player.pk, 'player_name': cgp.player.name, 'cardgameplayer_pk': cgp.pk, 'card_name': cgp.card.name, 'card_text': cgp.card.text, 'players': players}})  # notify everyone card was submitted

        # Draw new cards and send out to everyone, one by one
        Game.replenish_hands(content.get('game_code'))
        green_card = CardGamePlayer.objects.get(game=cgp.game, status=CardGamePlayer.MATCHING)
        for player in players:
            judge_name = 'you' if green_card.player.name == player.get('name') else green_card.player.name
            green_card_values = rename_card_fields(CardGamePlayer.objects.values('pk', 'card__name', 'card__text').get(game=cgp.game, status=CardGamePlayer.MATCHING))
            player_cards = list(CardGamePlayer.objects.filter(player__pk=player.get('pk'), game=cgp.game, status=CardGamePlayer.HAND).values('pk', 'card__name', 'card__text'))
            player_cards_renamed = []
            for card in player_cards:
                player_cards_renamed.append(rename_card_fields(card))
            multiplexer.group_send('player_{}'.format(player.get('pk')), 'new_cards', {'data': {'game_code': content.get('game_code'), 'judge_name': judge_name, 'green_card': green_card_values, 'cards': player_cards_renamed}})


class SubmitCardConsumer(JsonWebsocketConsumer):
    channel_session = True

    def receive(self, content, **kwargs):
        multiplexer = kwargs.get('multiplexer')
        cgp = CardGamePlayer.submit_card(content.get('cardgameplayer_pk'))
        player_cards = list(CardGamePlayer.objects.filter(player__pk=cgp.player.pk, game=cgp.game, status=CardGamePlayer.HAND).values('pk', 'card__name', 'card__text'))
        player_cards_renamed = []
        for card in player_cards:
            player_cards_renamed.append(rename_card_fields(card))
        submitted_cards = list(CardGamePlayer.objects.filter(game=cgp.game, status=CardGamePlayer.SUBMITTED).values('pk', 'card__name', 'card__text'))
        submitted_cards_renamed = []
        for card in submitted_cards:
            submitted_cards_renamed.append(rename_card_fields(card))
        multiplexer.group_send('player_{}'.format(cgp.player.pk), 'submit_card', {'data': {'game_code': content.get('game_code'), 'cards': player_cards_renamed}})
        players = list(cgp.game.players.values('pk', 'name', 'status', 'score'))
        multiplexer.group_send(content.get('game_code'), 'card_was_submitted', {'data': {'game_code': content.get('game_code'), 'player_pk': cgp.player.pk, 'player_name': cgp.player.name, 'players': players, 'cardgameplayer_pk': cgp.pk, 'card_name': cgp.card.name, 'card_text': cgp.card.text, 'submitted_cards': submitted_cards_renamed}})  # notify everyone card was submitted


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
