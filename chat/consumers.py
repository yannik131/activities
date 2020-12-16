import json
from django.utils import timezone
from channels.generic.websocket import WebsocketConsumer
from .models import ChatLogEntry, ChatRoom
from asgiref.sync import async_to_sync
from django.contrib.contenttypes.models import ContentType


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        app_label = self.scope['url_route']['kwargs']['app_label']
        model = self.scope['url_route']['kwargs']['model']
        id = self.scope['url_route']['kwargs']['id']
        ct = ContentType.objects.get(app_label=app_label, model=model)
        self.chat_room = ChatRoom.objects.get(target_ct=ct, target_id=id)
        self.room_name = f'{app_label}_{model}_{id}_chat'

        async_to_sync(self.channel_layer.group_add)(
            self.room_name,
            self.channel_name
        )

        self.accept()
        self.load_log()
        self.update_check()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_name,
            self.channel_name
        )

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        now = timezone.now()

        async_to_sync(self.channel_layer.group_send)(
            self.room_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': self.user.username,
                'datetime': now.isoformat()
            }
        )

        ChatLogEntry.objects.create(
            author=self.user,
            chat_room=self.chat_room,
            text=self.user.username + ', ' + now.strftime('%d.%m.%Y %H:%M:%S: ') + message,
            created=now)

        self.update_check()

    def update_check(self):
        check = self.user.last_chat_checks.get(room=self.chat_room)
        check.date = timezone.now()
        check.save()

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def fetch_log(self):
        entries = [entry.text.replace(self.user.username, 'Sie', 1) if entry.text.startswith(self.user.username) else entry.text for entry in self.chat_room.log_entries.all()]
        return entries

    def load_log(self):
        entries = self.fetch_log()
        self.send(text_data=json.dumps(
            {
                'type': 'load_log',
                'log': json.dumps(entries)
            }
        ))


