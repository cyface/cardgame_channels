import logging

from channels.test import ChannelTestCase, WSClient

from .game_logic import add_player_to_game
from .models import Player, Game, CardGamePlayer, Card

LOGGER = logging.getLogger("cardgame_channels_app")


class GameModelTests(ChannelTestCase):
    fixtures = ['test_card_data.json']  # 100 green and 100 red cards

    def setUp(self):
        self.game1 = Game.objects.create(pk=1, code='abcd')

    def test_cards(self):
        player = add_player_to_game(self.game1.code, 'tim')
        self.assertIsNotNone(str(player))
        self.assertEqual(6, len(player.cardgameplayer_set.all()))

        # Pull by CGP
        cgps_in_hand = CardGamePlayer.objects.filter(player=player, game=player.game, status=CardGamePlayer.HAND)
        self.assertEqual(5, len(cgps_in_hand))
        self.assertIsNotNone(str(cgps_in_hand[0]))

        # Pull by Card
        cards_in_hand = Card.objects.filter(cardgameplayer__player=player, cardgameplayer__game=player.game, cardgameplayer__status=CardGamePlayer.HAND)
        self.assertEqual(5, len(cards_in_hand))
        self.assertIsNotNone(str(cards_in_hand[0]))

    def test_game(self):
        self.assertIsNotNone(str(self.game1))


class GameConsumerTests(ChannelTestCase):
    fixtures = ['test_card_data.json']  # 100 green and 100 red cards

    def setUp(self):
        self.game1 = Game.objects.create(pk=1, code='abcd')

    def test_create_game(self):
        client = WSClient()

        while client.receive():
            pass  # Grab connection success message from each consumer

        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'create_game', 'payload': {}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'create_game')
        self.assertEqual(4, len(receive_reply.get('payload').get('data').get('game_code')))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_join_game_errors(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

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

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser

        # Joined Event to Player
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('join_game', receive_reply.get('stream'))

        # Player Joined Group Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('player_joined_game', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual('tim', data.get('player').get('name'))

        tim = Player.objects.get(name='tim')
        self.assertIsNotNone(Player.objects.get(name='tim', game__code='abcd'))
        self.assertEqual(6, len(tim.card_set.all()))  # 5 red, one green

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_validate_game_code(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Valid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'validate_game_code', 'payload': {'game_code': 'abcd'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'validate_game_code')
        self.assertEqual('abcd', receive_reply.get('payload').get('data').get('game_code'))
        self.assertTrue(receive_reply.get('payload').get('data').get('valid'))

        # Invalid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'validate_game_code', 'payload': {'game_code': '1234'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'validate_game_code')
        self.assertEqual('1234', receive_reply.get('payload').get('data').get('game_code'))
        self.assertFalse(receive_reply.get('payload').get('data').get('valid'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_validate_player_name(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Available Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'validate_player_name', 'payload': {'game_code': 'abcd', 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'validate_player_name')
        self.assertEqual('abcd', receive_reply.get('payload').get('data').get('game_code'))
        self.assertTrue(receive_reply.get('payload').get('data').get('valid'))

        # Invalid Test
        add_player_to_game(self.game1.code, 'tim')
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'validate_player_name', 'payload': {'game_code': 'abcd', 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'validate_player_name')
        self.assertEqual('abcd', receive_reply.get('payload').get('data').get('game_code'))
        self.assertFalse(receive_reply.get('payload').get('data').get('valid'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_pick_card(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Invalid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'pick_card', 'payload': {'game_code': '1234'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'pick_card')
        self.assertFalse(receive_reply.get('payload').get('data').get('valid'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_submit_card(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Invalid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'submit_card', 'payload': {'game_code': '1234'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'submit_card')
        self.assertFalse(receive_reply.get('payload').get('data').get('valid'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_boot_player(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Add extra player for valid test
        add_player_to_game(self.game1.code, 'tim')

        # Join Game
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': self.game1.code, 'player_name': 'bob'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        bob_pk = receive_reply.get('payload').get('data').get('player').get('pk')
        self.assertEqual('join_game', receive_reply.get('stream'))

        # Join Game Broadcast
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)

        # Valid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'boot_player', 'payload': {'game_code': self.game1.code, 'player_pk': bob_pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual(receive_reply.get('stream'), 'boot_player')
        self.assertEqual(self.game1.code, receive_reply.get('payload').get('data').get('game_code'))
        self.assertEqual('bob', receive_reply.get('payload').get('data').get('player_name'))
        self.assertTrue(receive_reply.get('payload').get('data').get('valid'))
        self.assertFalse(Player.objects.filter(pk=bob_pk))

        # Invalid Test
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'boot_player', 'payload': {'game_code': self.game1.code, 'player_pk': 99}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'boot_player')
        self.assertEqual(self.game1.code, receive_reply.get('payload').get('data').get('game_code'))
        self.assertFalse(receive_reply.get('payload').get('data').get('valid'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

    def test_whole_game(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client.receive():
            pass  # Grab connection success message from each consumer

        # Create a game
        client.send_and_consume('websocket.receive', path='/game/create/', text={'stream': 'create_game', 'payload': {}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual('create_game', receive_reply.get('stream'))
        game_code = receive_reply.get('payload').get('data').get('game_code')

        # Join the game
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': game_code, 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('join_game', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('tim', data.get('judge').get('name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player Join Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('player_joined_game', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual('tim', data.get('player').get('name'))

        # Set up player 2
        client2 = WSClient()
        client2.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
        while client2.receive():
            pass  # Grab connection success message from each consumer

        # Player 2: join the game
        client2.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': game_code, 'player_name': 'bob'}})  # Text arg is JSON as if it came from browser
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('join_game', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        submitted_card_pk = data.get('player_cards')[0].get('pk')
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('tim', data.get('judge').get('name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player2 Join Event
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('player_joined_game', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player').get('name'))
        self.assertEqual(2, len(data.get('players')))
        self.assertEqual('bob', data.get('players')[0].get('name'))
        self.assertEqual('tim', data.get('players')[1].get('name'))
        self.assertEqual('waiting', data.get('players')[0].get('status'))
        self.assertEqual('judge', data.get('players')[1].get('status'))

        # Player2 Join Event - Seen by Player 1
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual('player_joined_game', receive_reply.get('stream'))
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player').get('name'))

        # Player 2: Submit Card
        client2.send_and_consume('websocket.receive', path='/game/', text={'stream': 'submit_card', 'payload': {'game_code': game_code, 'card_pk': submitted_card_pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('submit_card', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(4, len(data.get('cards')))

        # Player 2: Submit Card - Group Notification
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('card_was_submitted', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('submitting_player').get('name'))

        # Player 1: Submit Card - Group Notification
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('card_was_submitted', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('submitting_player').get('name'))

        # Player 1 Pick Card - Group notification
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'pick_card', 'payload': {'game_code': game_code, 'card_pk': submitted_card_pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('pick_card', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('picked_player').get('name'))
        self.assertEqual(1, data.get('players')[0].get('score'))  # Point to bob
        self.assertEqual(0, data.get('players')[1].get('score'))  # Tim's score should not have changed

        # Player 2: Pick Card - Group notification
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertEqual('pick_card', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('picked_player').get('name'))
        self.assertEqual(1, data.get('players')[0].get('score'))  # Point to bob
        self.assertEqual(0, data.get('players')[1].get('score'))  # Tim's score should not have changed

        # Player 1: Get New Cards Message
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        self.assertEqual('new_cards', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(5, len(data.get('cards')))
        self.assertEqual('bob', data.get('judge').get('name'))  # Bob's card was picked so he should now be the judge
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player 2: Get New Cards Message
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        self.assertEqual('new_cards', receive_reply.get('stream'))
        data = receive_reply.get('payload').get('data')
        self.assertEqual(5, len(data.get('cards')))
        self.assertEqual('bob', data.get('judge').get('name'))  # Bob's card was picked so he should now be the judge
        self.assertIsNotNone(data.get('green_card').get('name'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()
