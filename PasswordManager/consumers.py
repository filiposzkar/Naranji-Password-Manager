import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
  async def connect(self):  # this is the receptionsit; when a user arrives on the chat page, this function decides how to let them in
    self.room_name = self.scope['url_route']['kwargs']['room_name']  # getting the room name from the URL (scope is like a request)
    self.room_group_name = f'chat_{self.room_name}' # creating an unique ID for the room in Redis, by appending the room name to the word "chat"

    await self.channel_layer.group_add( # the user is joining the room/group in Redis, so that the user will be notified of any new messages appearing the group
      self.room_group_name,
      self.channel_name
    )
    await self.accept()  # connection accepted, the door is opened for notifications

  async def disconnect(self, close_code):
    await self.channel_layer.group_discard(  # leaving the group
      self.room_group_name,
      self.channel_name
    )
  
  async def receive(self, text_data):  # receiving messages from the browser (JavaScript)
    data = json.loads(text_data)
    message = data['message']
    user = self.scope["user"]  # getting the logged-in user name
    username = user.username if user.is_authenticated else "Anonymous"

    await self.channel_layer.group_send( # broadcasting the message to everyone in this room vis Redis
      self.room_group_name, {
        'type': 'chat_message',
        'message': message,
        'username': username
      }
    )

  async def chat_message(self, event):  # receiving message from the Redis group
    message = event['message']
    username = event['username']

    await self.send(text_data=json.dumps ({  # sending the message to the browser
        'message': message,
        'username': username
    }))
