"""
WebSocket URL routing for PvP.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/pvp/room/(?P<room_id>\w+)/$', consumers.PvpGameConsumer.as_asgi()),
]
