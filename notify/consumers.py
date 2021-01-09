from itertools import cycle
import json
from account.models import User
from channels.generic.websocket import WebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from asgiref.sync import async_to_sync
from django.utils.timezone import now
from multiplayer.models import MultiplayerMatch
from multiplayer.utils import after, deal_cards, left_player


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
        data = match.game_data
        players = None
        if text_data['action'] == "request_data":
            if not match.in_progress:
                match.start()
            else:
                self.send(text_data=json.dumps(data))
        elif text_data['action'] in ["beating", "attacking"]:
            data["stacks"] = text_data["stacks"]
            data[self.user.username] = text_data["hand"]
            if not data["taking"]:
                data["done_list"] = json.dumps([])
            match.save()
            match.broadcast_data({
                "username": self.user.username,
                "action": "play",
                "stacks": data["stacks"],
                "n": text_data["n"]
            })
        elif text_data['action'] == "done":
            done_list = json.loads(data['done_list'])
            if(str(self.user.id) not in done_list):
                done_list.append(str(self.user.id))
            # defending player sends done when all is defended
            limit = match.member_limit
            if limit is 2 and len(done_list) is 2 or limit > 2 and len(done_list) is 3:
                players = json.loads(data["players"])
                if data["taking"]:
                    hand = json.loads(data[data["taking"]])
                    stacks = json.loads(data["stacks"])
                    for stack in stacks:
                        for card in stack:
                            hand.append(card)
                    data[data["taking"]] = json.dumps(hand)
                    data["attacking"] = left_player(data["taking"], players, data)
                    data["taking"] = ""
                else:
                    if json.loads(data[data["defending"]]):
                        data["attacking"] = data["defending"]
                    else:
                        data["attacking"] = left_player(data["defending"], players, data)
                deal_cards(data, players)
                data["defending"] = left_player(data["attacking"], players, data)
                done_list = []
                match.broadcast_data({
                    "action": "new_round",
                    "data": data
                })
            data['done_list'] = json.dumps(done_list)
            match.save()
        elif text_data["action"] == "take":
            players = json.loads(data["players"])
            data["done_list"] = json.dumps([str(self.user.id)])
            data["taking"] = self.user.username
            match.save()
            match.broadcast_data({
                "action": "take"
            })
        elif text_data["action"] == "transfer":
            players = json.loads(data["players"])
            data["stacks"] = text_data["stacks"]
            data[self.user.username] = text_data["hand"]
            data["done"] = json.dumps([])
            data["attacking"] = data["defending"]
            data["defending"] = left_player(data["attacking"], players, data)
            match.save()
            match.broadcast_data({
                "action": "transfer",
                "attacking": data["attacking"],
                "defending": data["defending"],
                "stacks": data["stacks"]
            })
        if players:
            count = 0
            for player in players:
                if json.loads(data[player]):
                    count += 1
            if count <= 1:
                match.start()
                match.broadcast_data(match.game_data)
        
    def chat_message(self, event):
        self.send(text_data=json.dumps(event))

    def notification(self, event):
        self.send(text_data=json.dumps(event))
        
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
