import logging

from channels.test import ChannelTestCase, WSClient

from .game_logic import add_player_to_game
from .models import Player, Game, CardGamePlayer, Card

LOGGER = logging.getLogger("cardgame_channels_app")


class GameConsumerTests(ChannelTestCase):
    fixtures = ['test_card_data.json']  # 100 green and 100 red cards

    def setUp(self):
        self.game1 = Game.objects.create(pk=1, code='abcd')

    def test_create_game(self):
        client = WSClient()

        try:
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'create_game', 'payload': {}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'create_game')
        self.assertEqual(4, len(receive_reply.get('payload').get('data').get('game_code')))
        client.session['game_code'] = receive_reply.get('payload').get('data').get('game_code')
        self.assertEqual(4, len(client.session.get('game_code')))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_join_game_errors(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        # Test Player Name Too Long
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': '1234567891011121314151617181920'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('most 10', receive_reply.get('payload').get('data').get('errors').get('player_name')[0])

        # Test Game Code Missing
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': '', 'player_name': '123456789'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('required', receive_reply.get('payload').get('data').get('errors').get('game_code')[0])

        # Test Player Name Missing
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': ''}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('required', receive_reply.get('payload').get('data').get('errors').get('player_name')[0])

        # Test Empty Submit
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': '', 'player_name': ''}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('required', receive_reply.get('payload').get('data').get('errors').get('game_code')[0])
        self.assertIn('required', receive_reply.get('payload').get('data').get('errors').get('player_name')[0])

        # Test Game Code Doesn't Exist
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': '1234', 'player_name': '123456789'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('does not exist', receive_reply.get('payload').get('data').get('errors').get('game_code')[0])

        # Test Player Name Taken
        add_player_to_game('abcd', 'my_player')
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': 'my_player'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIn('already taken', receive_reply.get('payload').get('data').get('errors').get('player_name')[0])
        Player.objects.get(name='my_player').delete()

        # Test HTML in Code/Player
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'a<b>', 'player_name': '&copy;<b>'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertIsNotNone(data.get('error'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_join_game(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser

        # Joined Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')

        # Player Joined Game Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual('tim', data.get('player').get('name'))

        tim = Player.objects.get(name='tim')
        self.assertIsNotNone(Player.objects.get(name='tim', game__code='abcd'))
        self.assertEqual(6, len(tim.card_set.all()))  # 5 red, one green

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_cards(self):
        player = add_player_to_game(self.game1.code, 'tim')
        self.assertEqual(6, len(player.cardgameplayer_set.all()))
        cards_in_hand = CardGamePlayer.objects.filter(player=player, game=player.game, status=CardGamePlayer.HAND)
        self.assertEqual(5, len(cards_in_hand))
        for card in cards_in_hand:
            LOGGER.debug(card)
        cards_in_hand = Card.objects.filter(cardgameplayer__player=player, cardgameplayer__game=player.game, cardgameplayer__status=CardGamePlayer.HAND).values('pk', 'name', 'text')
        for card in cards_in_hand:
            LOGGER.debug(card)
        self.assertEqual(5, len(cards_in_hand))

    def test_whole_game(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        # Create a game
        client.send_and_consume('websocket.receive', path='/game/create/', text={'stream': 'create_game', 'payload': {}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        game_code = receive_reply.get('payload').get('data').get('game_code')
        client.session['game_code'] = game_code

        # Join the game
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': game_code, 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('tim', data.get('judge').get('name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player Join Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual('tim', data.get('player').get('name'))
        client.session['player_pk'] = data.get('player').get('pk')
        client.session['player_name'] = data.get('player').get('name')

        client2 = WSClient()
        try:
            client2.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client2.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        # Player 2: join the game
        client2.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': game_code, 'player_name': 'bob'}})  # Text arg is JSON as if it came from browser
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        submitted_card_pk = data.get('player_cards')[0].get('pk')
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('tim', data.get('judge').get('name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player2 Join Event
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player').get('name'))
        self.assertEqual(2, len(data.get('players')))
        self.assertEqual('bob', data.get('players')[0].get('name'))
        self.assertEqual('tim', data.get('players')[1].get('name'))
        self.assertEqual('waiting', data.get('players')[0].get('status'))
        self.assertEqual('judge', data.get('players')[1].get('status'))
        client2.session['player_pk'] = data.get('player').get('pk')
        client2.session['player_name'] = data.get('player').get('name')

        # Player2 Join Event - Seen by Player 1
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player').get('name'))

        # Player 2: Submit Card
        client2.send_and_consume('websocket.receive', path='/game/', text={'stream': 'submit_card', 'payload': {'game_code': game_code, 'card_pk': submitted_card_pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(4, len(data.get('cards')))

        # Player 2: Submit Card - As seen by Player 1
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('submitting_player').get('name'))

        # Player 1: Pick Submitted Card
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'pick_card', 'payload': {'game_code': game_code, 'card_pk': submitted_card_pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('picked_player').get('name'))

        # Player 1: Get New Cards Message
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        stream = receive_reply.get('stream')
        self.assertEqual('new_cards', stream)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(5, len(data.get('cards')))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()
