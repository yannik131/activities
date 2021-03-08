from itertools import cycle
import json
from account.models import User
from channels.generic.websocket import WebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from asgiref.sync import async_to_sync
from django.utils.timezone import now
from multiplayer.models import MultiplayerMatch
from shared.shared import log


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        self.chat_room_cache = dict()
        self.user = User.objects.get(id=user_id)
        self.user.channel_name = self.channel_name
        self.user.save()
        async_to_sync(self.channel_layer.group_add)(
            self.user.channel_group_name,
            self.channel_name
        )
        self.accept()
        self.rtc_room_id = None
        self.match = None

    def disconnect(self, code):
        user = User.objects.get(id=self.user.id)
        user.channel_name = None
        user.save()
        if self.rtc_room_id:
            self.rtc_send({'action': 'disconnect'}, {'room_id': self.rtc_room_id})
        async_to_sync(self.channel_layer.group_discard)(
            self.user.channel_group_name,
            self.channel_name
        )
            
    def rtc(self, event):
        if event["sender"] != self.user.id:
            self.send(text_data=json.dumps(event))
            
    def rtc_send(self, data, text_data=None):
        data['type'] = 'rtc'
        data['sender'] = self.user.id
        if 'channel' in data:
            async_to_sync(self.channel_layer.group_send)(
                data['channel'],
                data
            )
        else:
            chat_room = self.chat_room_cache.setdefault(text_data['room_id'], ChatRoom.objects.get(id=text_data['room_id']))
            for member in chat_room.members.all():
                if member.channel_name:
                    async_to_sync(self.channel_layer.send)(
                        member.channel_name,
                        data
                    )
        
    def handle_rtc_message(self, text_data):
        if text_data["action"] == "join":
            self.rtc_send({
                'action': 'join'
            }, text_data)
            self.rtc_room_id = text_data['room_id']
        elif text_data['action'] == 'offer':
            self.rtc_send({
                'action': 'offer',
                'offer': text_data['offer'],
                'channel': text_data['channel']
            })
        elif text_data['action'] == 'answer':
            self.rtc_send({
                'action': 'answer',
                'answer': text_data['answer'],
                'channel': text_data['channel']
            })
        elif text_data['action'] == 'candidate':
            self.rtc_send({
                'action': 'candidate',
                'candidate': text_data['candidate'],
                'channel': text_data['channel']
            })
        elif text_data['action'] == 'leave':
            self.rtc_send({
                'action': 'leave'
            }, text_data)
        elif text_data['action'] == 'request_show':
            self.rtc_send({
                'action': 'request_show'
            }, text_data)
        elif text_data['action'] == 'show':
            self.rtc_send({
                'action': 'show',
                'live': text_data['live']
            }, text_data)

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        if not "type" in text_data:
            log("No type: ", self.user.username, text_data)
        if text_data["type"] == "chat":
            self.handle_chat_message(text_data)
        elif text_data["type"] == "multiplayer":
            self.handle_multiplayer_message(text_data)
        elif text_data['type'] == 'rtc':
            self.handle_rtc_message(text_data)

    def handle_chat_message(self, text_data):
        chat_room_id = text_data['id']
        chat_room = self.chat_room_cache.setdefault(chat_room_id, ChatRoom.objects.get(id=chat_room_id))
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
        if text_data["action"] == "match_list":
            self.send(text_data=json.dumps({
                'type': 'multiplayer',
                'action': 'match_list',
                'match_list': json.dumps(MultiplayerMatch.match_list_for(text_data["activity_id"]))
            }))
        elif text_data["action"] == "kick_user":
            if not self.match:
                self.match = MultiplayerMatch.objects.get(pk=text_data['match_id'])
            self.match.remove_member(User.objects.get(username=text_data['username']))
            
        
    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def notification(self, event):
        self.send(text_data=json.dumps(event))
        
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
