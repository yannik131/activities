import json
from channels.generic.websocket import WebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from multiplayer.models import MultiplayerMatch
from multiplayer.utils import before, deal_cards, left_player, player_with_cards
from redis import StrictRedis
conn = StrictRedis(host="localhost", port=6655)
import redis_lock
from asgiref.sync import async_to_sync
from shared.shared import log


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        
        async_to_sync(self.channel_layer.group_add)(
            f"match-{self.match_id}",
            self.channel_name
        )
        
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f"match-{self.match_id}",
            self.channel_name
        )
    
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
        
    def receive(self, text_data=None):
        with redis_lock.Lock(conn, self.match_id):
            text_data = json.loads(text_data)
            message = self.get_message(text_data)
            if not "data" in message:
                return
            if message["group"]:
                message["data"]["type"] = "multiplayer"
                async_to_sync(self.channel_layer.group_send)(
                    f"match-{self.match_id}",
                    message["data"]
                )
            else:
                self.send(text_data=json.dumps(message["data"]))
            
class DurakConsumer(GameConsumer):
    def get_message(self, text_data):
        match = MultiplayerMatch.objects.get(pk=self.match_id)
        data = match.game_data
        players = json.loads(data["players"])
        message = {"group": True}
        if text_data['action'] == "request_data":
            message["data"] = data
            message["group"] = False
            return message
        elif text_data['action'] in ["beating", "attacking"]:
            data["stacks"] = text_data["stacks"]
            data[self.username] = text_data["hand"]
            if not data["taking"]:
                data["done_list"] = json.dumps([])
            message["data"] = {
                "username": self.username,
                "action": "play",
                "stacks": data["stacks"],
                "n": text_data["n"]
            }
        elif text_data['action'] == "done":
            done_list = json.loads(data['done_list'])
            if(str(self.username) not in done_list):
                done_list.append(str(self.username))
            
            # defending player sends done when all is defended
            if len(done_list) == len(players):
                if data["taking"]:
                    hand = json.loads(data[data["taking"]])
                    stacks = json.loads(data["stacks"])
                    for stack in stacks:
                        for card in stack:
                            hand.append(card)
                    data[data["taking"]] = json.dumps(hand)
                    data["attacking"] = left_player(data["taking"], players, data)
                    data["taking"] = ""
                    deal_cards(data, players)
                else:
                    deal_cards(data, players)
                    if data["defending"]:
                        if json.loads(data[data["defending"]]):
                            data["attacking"] = data["defending"]
                        else:
                            data["attacking"] = left_player(data["defending"], players, data)
                    else:
                        data["attacking"] = None
                count = player_with_cards(players, data)
                if count <= 1:
                    durak = None
                    if count > 0 and json.loads(data[data["defending"]]):
                        durak = data["defending"]
                    match.start()
                    if durak:
                        data["defending"] = durak
                        data["attacking"] = before(durak, players)
                    message["data"] = match.game_data
                else:
                    data["defending"] = left_player(data["attacking"], players, data)
                    done_list = []
                    message["data"] = {
                        "action": "new_round",
                        "data": data
                    }
            data['done_list'] = json.dumps(done_list)
        elif text_data["action"] == "take":
            data["done_list"] = json.dumps([str(self.username)])
            data["taking"] = self.username
            message["data"] = {
                "action": "take"
            }
        elif text_data["action"] == "transfer":
            data["stacks"] = text_data["stacks"]
            data[self.username] = text_data["hand"]
            data["done_list"] = json.dumps([])
            data["attacking"] = data["defending"]
            data["defending"] = left_player(data["attacking"], players, data)
            message["data"] = {
                "action": "transfer",
                "attacking": data["attacking"],
                "attacking_n": len(json.loads(data[data["attacking"]])),
                "defending": data["defending"],
                "stacks": data["stacks"]
            }
        match.save()
        return message
            
class SkatConsumer(GameConsumer):
    def get_message(self, text_data):
        match = MultiplayerMatch.objects.get(pk=self.match_id)
        data = match.game_data
        message = {"group": True}
        if text_data["action"] == "request_data":
            message["data"] = data
            message["group"] = False
            return message
        elif text_data["action"] == "bid":
            bid = text_data["bid"]
            data["last_bid"] = bid
            data[f"{self.username}_bid"] = bid
            data["active"] = next_bidder(data)
        match.save()
        return message

class AudioConsumer(WebsocketConsumer):
    def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        
        async_to_sync(self.channel_layer.group_add)(
            f"audio-{self.match_id}",
            self.channel_name
        )
        
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f"audio-{self.match_id}",
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data = dict()
        text_data["type"] = "audio_message"
        text_data["sender"] = self.username
        text_data["bytes_data"] = bytes_data
        async_to_sync(self.channel_layer.group_send)(
            f"audio-{self.match_id}",
            text_data
        )

    def audio_message(self, event):
        if event["sender"] != self.username:
            self.send(bytes_data=event["bytes_data"])
    