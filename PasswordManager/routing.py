from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
  re_path(r'ws/credentials/$', consumers.CredentialConsumer.as_asgi()),
  re_path('ws/notes/$', consumers.NotesConsumer.as_asgi()),
]