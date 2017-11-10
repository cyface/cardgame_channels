from channels.test import ChannelTestCase, WSClient
import logging

from cardgame_channels_app.models import Game, Player

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

        client.send_and_consume('websocket.receive', path='/game/create/', text={'stream': 'create_game', 'payload': {}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'create_game')
        self.assertEqual(4, len(receive_reply.get('payload').get('data').get('game_code')))
        client.session['game_code'] = receive_reply.get('payload').get('data').get('game_code')
        self.assertEqual(4, len(client.session.get('game_code')))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/create/')
        disconnect_consumer.close()

    def test_join_game(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/abcd/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        client.send_and_consume('websocket.receive', path='/game/abcd/', text={'stream': 'join_game', 'payload': {'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'join_game')
        self.assertEqual('tim', receive_reply.get('payload').get('data').get('player_name'))

        tim = Player.objects.get(name='tim')
        self.assertIsNotNone(Player.objects.get(name='tim', game__code='abcd'))
        self.assertEqual(5, len(tim.card_set.all()))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/abcd/')
        disconnect_consumer.close()

    def test_submit_card(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/abcd/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
            while client.receive():
                pass  # Grab connection success message from each consumer
        except AssertionError:  # WS Client automatically checks that connection is accepted
            self.fail("Connection Rejected!")

        tim = Player.add_player_to_game('abcd', 'tim')
        self.assertIsNotNone(Player.objects.get(name='tim', game__code='abcd'))
        self.assertEqual(5, len(tim.card_set.all()))

        client.send_and_consume('websocket.receive', path='/game/abcd/', text={'stream': 'submit_card', 'payload': {'cardgameplayer_pk': tim.cardgameplayer_set.all()[0].pk}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        self.assertEqual(receive_reply.get('stream'), 'submit_card')
        self.assertIsNotNone(receive_reply.get('payload').get('data').get('card_name'))
        self.assertIsNotNone(receive_reply.get('payload').get('data').get('player_pk'))

        self.assertEqual(1, len(tim.cardgameplayer_set.filter(status='submitted')))

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/abcd/')
        disconnect_consumer.close()

    def test_whole_game(self):
        client = WSClient()

        try:
            client.send_and_consume('websocket.connect', path='/game/abcd/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
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
        client.send_and_consume('websocket.receive', path='/game/{}/'.format(game_code), text={'stream': 'join_game', 'payload': {'player_name': 'tim'}})  # Text arg is JSON as if it came from browser
        receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
        player_pk = receive_reply.get('payload').get('data').get('player_pk')
        player_name = receive_reply.get('payload').get('data').get('player_name')
        client.session['player_pk'] = player_pk
        client.session['player_name'] = player_name

        # Submit Card
        # @TODO: Submit Card - but can't until the cgp ids are coming back

        disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/game/abcd/')
        disconnect_consumer.close()
