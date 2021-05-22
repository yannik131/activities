from itertools import cycle
import json
from account.models import User, LocationMarker
from channels.generic.websocket import WebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from asgiref.sync import async_to_sync
from django.utils.timezone import now
from multiplayer.models import MultiplayerMatch
from shared.shared import log
from chat.utils import broadcast
from multiplayer.utils import change
from activity.models import Activity
from wall.models import Post
from character.models import Global
from django.template.loader import render_to_string
from django.utils import translation
from redis import StrictRedis
conn = StrictRedis(host="localhost", port=6655)
import redis_lock


class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        user_id = self.scope['url_route']['kwargs']['user_id']
        self.user = User.objects.get(id=user_id)
        key = self.scope['url_route']['kwargs']['key']
        if self.user.channel_name:
            async_to_sync(self.channel_layer.send)(
                self.user.channel_name,
                {'type': 'notification', 'action': 'close'}
            )
        if self.user.ws_key != key:
            self.user = None
            return
        self.user.channel_name = self.channel_name
        self.user.save()
        async_to_sync(self.channel_layer.group_add)(
            self.user.channel_group_name,
            self.channel_name
        )
        self.accept()
        self.rtc_room_id = None

    def disconnect(self, code):
        if not self.user:
            return
        user = User.objects.get(id=self.user.id)
        user.channel_name = None
        user.save()
        if self.rtc_room_id:
            self.rtc_send({'action': 'disconnect', 'user_id': user.id, 'username': self.user.username}, {'room_id': self.rtc_room_id})
        async_to_sync(self.channel_layer.group_discard)(
            self.user.channel_group_name,
            self.channel_name
        )
            
    def rtc(self, event):
        if event["user_id"] != self.user.id:
            self.send(text_data=json.dumps(event))
            
    def rtc_send(self, data, text_data=None):
        data['type'] = 'rtc'
        data['user_id'] = self.user.id
        if 'channel' in data:
            data['room_id'] = self.rtc_room_id
            async_to_sync(self.channel_layer.group_send)(
                data['channel'],
                data
            )
        else:
            data['room_id'] = text_data.get('room_id', self.rtc_room_id)
            chat_room = ChatRoom.objects.get(id=data['room_id'])
            for member in chat_room.members.all():
                if member.channel_name:
                    async_to_sync(self.channel_layer.send)(
                        member.channel_name,
                        data
                    )

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        if text_data["type"] == "chat":
            self.handle_chat_message(text_data)
        elif text_data["type"] == "multiplayer":
            self.handle_multiplayer_message(text_data)
        elif text_data['type'] == 'rtc':
            self.handle_rtc_message(text_data)
        elif text_data['type'] == 'character':
            self.handle_character_message(text_data)
        elif text_data['type'] == 'wall':
            self.handle_wall_message(text_data)
        elif text_data['type'] == 'map':
            self.handle_map_message(text_data)

    def handle_chat_message(self, text_data):
        if text_data['action'] == 'sent':
            self.distribute_chat_message(text_data)
        elif text_data['action'] == 'room':
            self.generate_chat_window(text_data)
        elif text_data['action'] == 'list':
            self.generate_chat_list(text_data)
               
    def distribute_chat_message(self, text_data):
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
        
        broadcast(chat_room.members.all(), {
            'type': 'chat_message',
            'room_id': chat_room_id,
            'message': text_data['message'],
            'username': self.user.username,
            'time': timestr,
            'origin': log.full_origin(self.user),
            'action': 'sent'
        })
            
    def generate_chat_list(self, text_data):
        with translation.override(text_data['language_code']):
            rooms = []
            for room in self.user.chat_rooms.all():
                rooms.append((room, room.get_target(self.user)))
            if not rooms:
                self.send(json.dumps({
                    'type': 'chat_message',
                    'action': 'list',
                })) 
                return
            rooms_with_news = self.user.rooms_with_news()
            rooms = sorted(rooms, key=lambda t: t[0].target_ct.model)
            rooms = sorted(rooms, key=lambda t: 1 if t[0].id in rooms_with_news else 0, reverse=True)
            chat_list = render_to_string('chat/chat_list.html', dict(rooms=rooms, rooms_with_news=self.user.rooms_with_news(), rooms_with_news_count=len(rooms_with_news), friendship=rooms[0][0].target_ct.model == "friendship" if len(rooms) else None))
            self.send(json.dumps({
                'type': 'chat_message',
                'action': 'list',
                'html': chat_list
            })) 
        
    def generate_chat_window(self, text_data):
        room = ChatRoom.objects.get(pk=text_data['id'])
        try:
            self.user.last_chat_checks.get(room=room).update()
        except ChatCheck.DoesNotExist:
            return
        chat_window = render_to_string('chat/chat_window.html', dict(room=room, user=self.user, friendship=room.target_ct.model == 'friendship'))
        self.send(json.dumps({
            'type': 'chat_message',
            'action': 'room',
            'html': chat_window,
            'id': room.id
        }))
    
    def handle_multiplayer_message(self, text_data):
        if text_data["action"] == "match_list":
            self.send(text_data=json.dumps({
                'type': 'multiplayer',
                'action': 'match_list',
                'match_list': json.dumps(MultiplayerMatch.match_list_for(text_data["activity_id"]))
            }))
        elif text_data["action"] == "kick_user":
            match = MultiplayerMatch.objects.get(pk=text_data['match_id'])
            match.remove_member(User.objects.get(username=text_data['username']))
        elif text_data['action'] == 'start':
            with redis_lock.Lock(conn, str(text_data['match_id'])):
                match = MultiplayerMatch.objects.get(pk=text_data['match_id'])
                if match.is_full() and not match.in_progress:
                    match.start()
            
    def handle_rtc_message(self, text_data):
        if text_data["action"] == "join":
            self.rtc_room_id = text_data['room_id']
            self.rtc_send({
                'action': 'join'
            }, text_data)
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
                'action': 'leave',
                'username': self.user.username
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
            
    def handle_character_message(self, text_data):
        if text_data['action'] == 'back':
            user = User.objects.get(id=self.user.id)
            user.character.current_question -= 1
            change(user.character.traits, text_data['trait'], -text_data['value'])
            user.character.save()
        elif text_data['action'] == 'next':
            user = User.objects.get(id=self.user.id)
            user.character.current_question += 1
            change(user.character.traits, text_data['trait'], text_data['value'])
            user.character.save()
        elif text_data['action'] == 'weights':
            activity = Activity.objects.get(id=text_data['id'])
            activity.trait_weights = json.loads(text_data['weights'])
            activity.save()
        elif text_data['action'] == 'done':
            Global.normalize_traits()
            
    def handle_wall_message(self, text_data):
        post = Post.objects.get(pk=text_data['id'])
        if text_data['action'] == 'like':
            post.liked_by.add(self.user)
        elif text_data['action'] == 'dislike':
            post.disliked_by.add(self.user)
        elif text_data['action'] == 'remove_like':
            post.liked_by.remove(self.user)
        elif text_data['action'] == 'remove_dislike':
            post.disliked_by.remove(self.user)
            
    def handle_map_message(self, text_data):
        try:
            LocationMarker.objects.get_or_create(
                description=text_data['description'], 
                latitude=text_data['lat'], 
                longitude=text_data['lon'], 
                author=self.user, 
                location=self.user.location, 
                activity=Activity.objects.get(pk=text_data['activity'])
            )
        except:
            pass
    
    def wall_message(self, post, action):
        event = {
            'type': 'wall',
            'post_id': post.id,
            'action': action
        }
        self.send(text_data=json.dumps(event))
    
    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def notification(self, event):
        self.send(text_data=json.dumps(event))
        
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
