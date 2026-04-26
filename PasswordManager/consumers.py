import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CredentialConsumer (AsyncWebsocketConsumer):
  async def connect(self):  # when the browser opens the page and runs "new WebSocket()", this function tunes the user into a frequency called "credentials_group"
    await self.channel_layer.group_add("credentials_group", self.channel_name)
    await self.accept()

  async def disconnect(self, code): # if the user closes the tab, it removes them from the frequency, so that the server won't send data to a ghost
    if self.channel_layer:
      await self.channel_layer.group_discard("credentials_group", self.channel_name)
  
  async def broadcast_new_item(self, event):  # when the fake loop generates a new item, it tells this function to broadcast it (to display it to the user)
    item = event['item']
    await self.send(text_data=json.dumps(item))  # sending the actual data to the frontend


class NotesConsumer (AsyncWebsocketConsumer):
  async def connect(self):  # when the browser opens the page and runs "new WebSocket()", this function tunes the user into a frequency called "credentials_group"
    await self.channel_layer.group_add("notes_group", self.channel_name)
    await self.accept()

  async def disconnect(self, code): # if the user closes the tab, it removes them from the frequency, so that the server won't send data to a ghost
    if self.channel_layer:
      await self.channel_layer.group_discard("notes_group", self.channel_name)
  
  async def broadcast_new_item(self, event):  # when the fake loop generates a new item, it tells this function to broadcast it (to display it to the user)
    item = event['item']
    await self.send(text_data=json.dumps(item))  # sending the actual data to the frontend