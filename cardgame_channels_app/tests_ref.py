# from channels.test import ChannelTestCase, WSClient, Client
# import logging
#
# LOGGER = logging.getLogger("cardgame_channels_app")
#
#
# class ConsumerTests(ChannelTestCase):
#     def test_websockets_consumer(self):
#         #  Create a channels test client
#         client = Client()
#
#         #  Send a websocket.connect message, passing in the path so it maps to the right consumer via the routing in routing.py
#         #  Consume portion maps that message to a consumer and runs and returns an instance of the consumer
#         connect_consumer = client.send_and_consume('websocket.connect', {'path': '/game/123/'})
#         connect_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(connect_reply, {'accept': True})  # websocket.connect should return acceptance of connection
#
#         receive_consumer = client.send_and_consume('websocket.receive', {'path': '/game/123/', 'text': 'text'})
#         receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply, {'text': 'textreply'})
#
#         receive_consumer.group_send('123', text='grouptext')  # This sends a message out to a group - shortcut off of the Websocket Consumer
#         group_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(group_reply, {'text': 'grouptext'})
#
#         disconnect_consumer = client.send_and_consume('websocket.disconnect', {'path': '/game/123/'})
#         disconnect_consumer.close()
#
#     def test_json_websockets_consumer(self):
#         client = WSClient()
#
#         try:
#             client.send_and_consume('websocket.connect', path='/gamej/321/')
#         except AssertionError:  # WS Client automatically checks that connection is accepted
#             self.fail("Connection Rejected!")
#
#         receive_consumer = client.send_and_consume('websocket.receive', path='/gamej/321/', text={'text': 'text'})  # Text arg is JSON as if it came from browser
#         receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply, {'text': 'textreply'})
#
#         group_content = {'key1': 'value', 'key2': 2}
#         receive_consumer.group_send('321', content=group_content)
#         group_reply = client.receive()
#         self.assertEqual(group_reply, group_content)
#
#         disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/gamej/321/')
#         disconnect_consumer.close()
#
#     def test_multiplex_json_websockets_consumer(self):
#         client = WSClient()
#
#         try:
#             client.send_and_consume('websocket.connect', path='/gamem/4321/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
#             client.receive()  # Grab connection success message from 1st consumer
#             client.receive()  # Grab connection success message from 2nd consumer
#         except AssertionError:  # WS Client automatically checks that connection is accepted
#             self.fail("Connection Rejected!")
#
#         receive_consumer = client.send_and_consume('websocket.receive', path='/gamem/4321/', text={'stream': 'echo', 'payload': {'text': 'text'}})  # Text arg is JSON as if it came from browser
#         receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply, {'payload': {'original_message': {'text': 'text'}}, 'stream': 'echo'})
#
#         group_content = {'key1': 'value', 'key2': 2}
#         receive_consumer.multiplexer_class.group_send('4321', stream='echo', payload=group_content)  # MultiplexerClass is set to WebsocketMultiplexer by default
#         group_reply = client.receive()  # Pull group message off of reply channel
#         LOGGER.debug(group_reply)
#         self.assertEqual(group_reply, {'stream': 'echo', 'payload': {'key1': 'value', 'key2': 2}})
#
#         disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/gamem/4321/')
#         disconnect_consumer.close()
#
#     def test_multi_multiplex_json_websockets_consumer(self):
#         """Tests multiple clients connecting, and all receiving group messages"""
#         client = WSClient()
#         client2 = WSClient()
#
#         try:
#             client.send_and_consume('websocket.connect', path='/gamem/54321/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
#             client.receive()  # Grab connection success message from 1st consumer
#             client.receive()  # Grab connection success message from 2nd consumer
#         except AssertionError:  # WS Client automatically checks that connection is accepted
#             self.fail("Connection Rejected!")
#
#         try:
#             client2.send_and_consume('websocket.connect', path='/gamem/54321/')  # Connect is forwarded to ALL multiplexed consumers under this demultiplexer
#             client2.receive()  # Grab connection success message from 1st consumer
#             client2.receive()  # Grab connection success message from 2nd consumer
#         except AssertionError:  # WS Client automatically checks that connection is accepted
#             self.fail("Connection Rejected!")
#
#         receive_consumer1 = client.send_and_consume('websocket.receive', path='/gamem/54321/', text={'stream': 'echo', 'payload': {'text': 'text1'}})  # Text arg is JSON as if it came from browser
#         receive_reply1 = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply1, {'payload': {'original_message': {'text': 'text1'}}, 'stream': 'echo'})
#
#         receive_consumer2 = client2.send_and_consume('websocket.receive', path='/gamem/54321/', text={'stream': 'echo', 'payload': {'text': 'text2'}})  # Text arg is JSON as if it came from browser
#         receive_reply2 = client2.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply2, {'payload': {'original_message': {'text': 'text2'}}, 'stream': 'echo'})
#
#         group_content = {'key1': 'value', 'key2': 2}
#         receive_consumer1.multiplexer_class.group_send('54321', stream='echo', payload=group_content)  # MultiplexerClass is set to WebsocketMultiplexer by default
#         group_reply1 = client.receive()  # Pull group message off of reply channel
#         self.assertEqual(group_reply1, {'stream': 'echo', 'payload': {'key1': 'value', 'key2': 2}})
#         group_reply2 = client2.receive()  # Pull group message off of reply channel
#         self.assertEqual(group_reply2, {'stream': 'echo', 'payload': {'key1': 'value', 'key2': 2}})
#
#         disconnect_consumer = client.send_and_consume('websocket.disconnect', path='/gamem/54321/')
#         disconnect_consumer.close()
#
#
# class MyBindingTests(ChannelTestCase):
#     def test_binding(self):
#         #  Create a channels test client
#         client = WSClient()
#
#         #  Send a websocket.connect message, passing in the path so it maps to the right consumer via the routing in routing.py
#         #  Consume portion maps that message to a consumer and runs and returns an instance of the consumer
#         try:
#             client.send_and_consume('websocket.connect', path='/integer/')
#             client.receive()
#         except AssertionError:  # WS Client automatically checks that connection is accepted
#             self.fail("Connection Rejected!")
#
#         # Create a IntegerValue via databinding - note 'action' and 'data' elements in the payload, which are required
#         receive_consumer = client.send_and_consume('websocket.receive', path='/integer/', text={'stream': 'intval', 'payload': {'action': 'create', 'data': {'name': 'int0', 'value': 1}}})
#         receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply, {'stream': 'intval', 'payload': {'action': 'create', 'pk': 2, 'data': {'name': 'int0', 'value': 1}, 'model': 'channels_simple_app.integervalue'}})
#
#         # Validate that Integer Value was Created
#         all_integer_values = IntegerValue.objects.all()
#         self.assertEqual(2, len(all_integer_values))
#         self.assertEqual('int0', all_integer_values[1].name)
#         self.assertEqual(1, all_integer_values[1].value)
#
#         # Create IntegerValue directly, make sure we get notified
#         IntegerValue.objects.create(pk=3, name='int2', value=2)
#         receive_reply = client.receive()
#         self.assertEqual(receive_reply, {'stream': 'intval', 'payload': {'action': 'create', 'pk': 3, 'data': {'name': 'int2', 'value': 2}, 'model': 'channels_simple_app.integervalue'}})
#
#         # Update IntegerValue directly, make sure we get notified
#         integer_value_to_update = IntegerValue.objects.get(pk=3)
#         integer_value_to_update.value = 3
#         integer_value_to_update.save()
#         receive_reply = client.receive()
#         self.assertEqual(receive_reply, {'stream': 'intval', 'payload': {'action': 'update', 'pk': 3, 'data': {'name': 'int2', 'value': 3}, 'model': 'channels_simple_app.integervalue'}})
#
#         # Update a IntegerValue via databinding - note 'action', 'pk', and 'data' elements in the payload, which are required
#         update_consumer = client.send_and_consume('websocket.receive', path='/integer/', text={'stream': 'intval', 'payload': {'action': 'update', 'pk': 1, 'data': {'value': 5}}})
#         receive_reply = client.receive()  # receive() grabs the content of the next message off of the client's reply_channel
#         self.assertEqual(receive_reply, {'stream': 'intval', 'payload': {'action': 'update', 'pk': 1, 'data': {'name': 'int1', 'value': 5}, 'model': 'channels_simple_app.integervalue'}})
#
#         # Validate that Integer Value was Updated
#         integer_value_int1 = IntegerValue.objects.get(pk=1)
#         self.assertEqual('int1', integer_value_int1.name)
#         self.assertEqual(5, integer_value_int1.value)
#
#         # Retrieve a IntegerValue via websocket request - note 'stream' and 'payload' which are required
#         update_consumer = client.send_and_consume('websocket.receive', path='/integer/', text={'stream': 'intval_get', 'payload': {'pk': 1}})
#         receive_reply = client.receive()
#         self.assertEqual(receive_reply, {'stream': 'intval_get', 'payload': {'action': 'get', 'data': {'name': 'int1', 'value': 5}, 'pk': 1}})
#
#         disconnect_consumer = client.send_and_consume('websocket.disconnect', {'path': '/integer/'})
#         disconnect_consumer.close()
