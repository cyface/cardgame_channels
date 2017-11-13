import logging

from channels.test import ChannelTestCase, WSClient

from cardgame_channels_app.models import Player, Game

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

    def test_join_game(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'join_game', 'payload': {'game_code': 'abcd', 'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('you', data.get('judge_name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        tim = Player.objects.get(name='tim')
        self.assertIsNotNone(Player.objects.get(name='tim', game__code='abcd'))
        self.assertEqual(6, len(tim.card_set.all()))  # 5 red, one green

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()

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
        self.assertEqual(1, len(data.get('players')))
        self.assertEqual('judge', data.get('players')[0].get('status'))
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('you', data.get('judge_name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player Join Event
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('tim', data.get('player_name'))
        client.session['player_pk'] = data.get('player_pk')
        client.session['player_name'] = data.get('player_name')

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
        submitted_card = data.get('player_cards')[0].get('pk')
        self.assertEqual(2, len(data.get('players')))
        self.assertEqual('bob', data.get('players')[0].get('name'))
        self.assertEqual('tim', data.get('players')[1].get('name'))
        self.assertEqual('waiting', data.get('players')[0].get('status'))
        self.assertEqual('judge', data.get('players')[1].get('status'))
        self.assertEqual(5, len(data.get('player_cards')))
        self.assertEqual('tim', data.get('judge_name'))
        self.assertIsNotNone(data.get('green_card').get('name'))

        # Player2 Join Event
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player_name'))
        client2.session['player_pk'] = data.get('player_pk')
        client2.session['player_name'] = data.get('player_name')

        # Player2 Join Event - Seen by Player 1
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player_name'))

        # Player 2: Submit Card
        client2.send_and_consume('websocket.receive', path='/game/', text={'stream': 'submit_card', 'payload': {'game_code': game_code, 'cardgameplayer_pk': submitted_card}})  # Text arg is JSON as if it came from browser
        receive_reply = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player_name'))

        # Player 2: Submit Card - As seen by Player 1
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player_name'))

        # Player 1: Pick Submitted Card
        client.send_and_consume('websocket.receive', path='/game/', text={'stream': 'pick_card', 'payload': {'game_code': game_code, 'cardgameplayer_pk': submitted_card}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        LOGGER.debug(receive_reply)
        self.assertIsNotNone(receive_reply)
        data = receive_reply.get('payload').get('data')
        self.assertEqual('bob', data.get('player_name'))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/')
        disconnect_consumer.close()
