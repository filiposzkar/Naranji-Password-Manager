from django.urls import re_path
from . import consumers

websocket_urlpatterns = [  # this tells Django which consumer to use when a user connects to a specific address
  # this matches ws://127.0.0.1:8000/ws/chat/room_name/
  re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]