import json
from account.models import User
from channels.generic.websocket import WebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from asgiref.sync import async_to_sync
from django.utils.timezone import now
from multiplayer.models import MultiplayerMatch


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = User.objects.get(id=user_id)
        self.user.channel_name = self.channel_name
        self.user.save()
        async_to_sync(self.channel_layer.group_add)(
            self.user.channel_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.user.channel_group_name,
            self.channel_name
        )
        user = User.objects.get(id=self.user.id)
        user.channel_name = None
        user.save()

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        if text_data["type"] == "chat":
            self.handle_chat_message(text_data)
        if text_data["type"] == "multiplayer":
            self.handle_multiplayer_message(text_data)

    def handle_chat_message(self, text_data):
        chat_room_id = text_data['id']
        chat_room = ChatRoom.objects.get(id=chat_room_id)
        if 'update_check' in text_data:
            self.user.last_chat_checks.get(room=chat_room).update()
            return
        time = now()
        timestr = time.isoformat()

        log = ChatLogEntry.objects.create(
            author=self.user,
            chat_room=chat_room,
            text=text_data['message'],
            created=time)

        for member in chat_room.members.all():
            if member.channel_name:
                async_to_sync(self.channel_layer.send)(
                    member.channel_name,
                    {
                        'type': 'chat_message',
                        'id': chat_room_id,
                        'message': text_data['message'],
                        'username': self.user.username,
                        'time': timestr,
                        'origin': log.full_origin(self.user),
                        'url': chat_room.get_absolute_url()
                    }
                )
                
    def handle_multiplayer_message(self, text_data):
        match = MultiplayerMatch.objects.get(pk=text_data['match_id'])
        if text_data['action'] == "request_data":
            if not match.in_progress:
                match.start()
            else:
                self.send(text_data=json.dumps(match.game_data))
        elif text_data['action'] == "play":
            match.game_data["stacks"] = text_data["stacks"]
            match.game_data[self.user.username] = text_data["hand"]
            match.game_data["done"] = json.dumps([])
            match.save()
            match.broadcast_data({
                "type": "multiplayer",
                "username": self.user.username,
                "action": "play",
                "stacks": match.game_data["stacks"],
                "n": text_data["n"]
            })
        elif text_data['action'] == "done":
            done_list = json.loads(match.game_data['done'])
            if(str(self.user.id) not in done_list):
                done_list.append(str(self.user.id))
            if len(done_list) == 2:
                match.game_data["stacks"] = json.dumps([])
                
            match.game_data['done'] = json.dumps(done_list)
            if 
        

    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def notification(self, event):
        self.send(text_data=json.dumps(event))
        
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
