import json
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatLogEntry, ChatRoom
from asgiref.sync import sync_to_async
from django.contrib.contenttypes.models import ContentType


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        app_label = self.scope['url_route']['kwargs']['app_label']
        model = self.scope['url_route']['kwargs']['model']
        id = self.scope['url_route']['kwargs']['id']
        ct = await sync_to_async(ContentType.objects.get)(app_label=app_label, model=model)
        self.chat_room = await sync_to_async(ChatRoom.objects.get)(target_ct=ct, target_id=id)
        self.room_name = f'{app_label}_{model}_{id}_chat'

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()
        await self.load_log()
        await sync_to_async(self.update_check)()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        now = timezone.now()

        await self.channel_layer.group_send(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat()
            }
        )

        await sync_to_async(ChatLogEntry.objects.create)(
            author=self.user,
            chat_room=self.chat_room,
            text=self.user.username + ', ' + now.strftime('%d.%m.%Y %H:%M:%S Uhr: ') + message,
            created=now)

        await sync_to_async(self.update_check)()

    def update_check(self):
        check = self.user.last_chat_checks.get(room=self.chat_room)
        check.date = timezone.now()
        check.save()

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    def fetch_log(self):
        entries = [entry.text.replace(self.user.username, 'Sie', 1) if entry.text.startswith(self.user.username) else entry.text for entry in self.chat_room.log_entries.all()]
        return entries

    async def load_log(self):
        entries = await sync_to_async(self.fetch_log)()
        await self.send(text_data=json.dumps(
            {
                'type': 'load_log',
                'log': json.dumps(entries)
            }
        ))


