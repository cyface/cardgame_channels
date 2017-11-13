from channels.routing import route_class

from cardgame_channels_app.consumers import GameDemultiplexer

channel_routing = [
    route_class(GameDemultiplexer, path=r"^/game/"),
]
