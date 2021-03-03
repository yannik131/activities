import json
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from multiplayer.models import MultiplayerMatch
from multiplayer.utils import *
from redis import StrictRedis
conn = StrictRedis(host="localhost", port=6655)
import redis_lock
from asgiref.sync import async_to_sync
from shared.shared import log


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        if MultiplayerMatch.objects.filter(pk=self.match_id).exists():
            async_to_sync(self.channel_layer.group_add)(
                f"match-{self.match_id}",
                self.channel_name
            )
            self.rtc_send({'action': 'channel_name', 'name': self.channel_name})
            
            self.accept()

    def disconnect(self, code):
        self.rtc_send({'action': 'disconnect'})
        async_to_sync(self.channel_layer.group_discard)(
            f"match-{self.match_id}",
            self.channel_name
        )
    
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
        
    def rtc(self, event):
        if event["sender"] != self.username or event['action'] == 'channel_name':
            self.send(text_data=json.dumps(event))
            
    def rtc_send(self, data):
        data['type'] = 'rtc'
        data['sender'] = self.username
        if 'channel' in data:
            log(self.username, "sends offer to", data['channel'])
            async_to_sync(self.channel_layer.send)(
                data['channel'],
                data
            )
        else:
            async_to_sync(self.channel_layer.group_send)(
                f"match-{self.match_id}",
                data
            )
        
    def handle_rtc_message(self, text_data):
        if text_data["action"] == "join":
            self.rtc_send({
                'action': 'join'
            })
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
            })
        elif text_data['action'] == 'channel_request':
            self.rtc_send({
                'action': 'channel_request',
                'origin': self.channel_name
            })
        elif text_data['action'] == 'channel_name':
            async_to_sync(self.channel_layer.send)(
                text_data['origin'],
                {
                    'type': 'rtc',
                    'action': 'channel_name',
                    'sender': self.username,
                    'name': self.channel_name
                }
            )
        
    def receive(self, text_data=None):
        text_data = json.loads(text_data)
        if "type" in text_data and text_data["type"] == "rtc":
            self.handle_rtc_message(text_data)
            return
        with redis_lock.Lock(conn, self.match_id):
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
            if not data["first"] and len(json.loads(text_data["hand"])) == 0:
                data["first"] = self.username
            if not data["taking"]:
                data["done_list"] = json.dumps([])
            message["data"] = {
                "username": self.username,
                "action": "play",
                "stacks": data["stacks"],
                "n": text_data["n"],
                "defending": data["defending"],
                "attacking": data["attacking"]
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
                players_with_cards = get_players_with_cards(players, data)
                if len(players_with_cards) <= 1:
                    durak = None
                    if players_with_cards:
                        durak = players_with_cards[0]
                    summary = give_durak_points(data, players, durak)
                    match.start_durak()
                    if durak:
                        data["defending"] = durak
                        data["attacking"] = before(durak, players)
                    else:
                        data["attacking"] = data["first"]
                        data["defending"] = after(data["attacking"], players)
                    message["data"] = match.game_data
                    message["data"]["summary"] = summary
                    message["data"]["game_number"] = data["game_number"]
                else:
                    data["defending"] = left_player(data["attacking"], players, data)
                    data["started"] = data["attacking"]
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
            if not data["first"] and len(json.loads(text_data["hand"])) == 0:
                data["first"] = self.username
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
        elif text_data["action"] == "play":
            handle_play("skat", data, text_data, self.username, message, match)
        elif text_data["action"] == "declare":
            data["game_type"] = text_data["game"][0]
            data["declarations"] += text_data["game"][1:]
            data["solist"] = data["active"]
            data["active"] = data["forehand"]
            data["mode"] = "playing"
            data["factor"] = determine_factor(data)
            message["data"] = {
                "action": "start",
                "active": data["active"],
                "game_type": data["game_type"],
                "solist": data["solist"],
                data["solist"]: data[data["solist"]],
                "declarations": data["declarations"]
            }
        elif text_data["action"] == "put":
            data["deck"] = text_data["skat"]
            data[data["active"]] = text_data["hand"]
            data["mode"] = "declaring"
            message["data"] = {
                "action": "declare"
            }
        elif text_data["action"] == "take":
            message["data"] = {
                "action": "take",
                "deck": data["deck"]
            }
            hand = json.loads(data[data["active"]])
            hand += json.loads(data["deck"])
            data[data["active"]] = json.dumps(hand)
            data["deck"] = json.dumps([])
            data["mode"] = "putting"
        elif text_data["action"] == "no_take":
            data["mode"] = "declaring"
            data["declarations"] += "h"
            message["data"] = {
                "action": "declare"
            }
            message["group"] = False
        elif text_data["action"] == "bid":
            bid = text_data["bid"]
            data[f"{self.username}_bid"] = bid
            if bid == "pass":
                data["passed"] += "x"
            else:
                data["highest_bid"] = json.dumps([bid, self.username])
            
            data["last_bid"] = json.dumps([bid, self.username])
            bidder, more = next_bidder(data)
            data["more"] = more
            if bidder:
                data["active"] = bidder
            message["data"] = {
                "action": "bid",
                "last_bid": data["last_bid"],
                "highest_bid": data["highest_bid"],
                "active": data["active"],
                "more": more,
                "mode": "bidding"
            }
            
            if data["highest_bid"] and len(data["passed"]) == 2:
                data["mode"] = "taking"
                message["data"]["mode"] = "taking"
            elif len(data["passed"]) == 3:
                players = json.loads(data["players"])
                match.start_skat()
                data["started"] = after(data["started"], players)
                data["forehand"] = data["started"]
                data["active"] = after(data["forehand"], players)
                message["data"]["round"] = match.game_data
        match.save()
        return message

class DoppelkopfConsumer(GameConsumer):
    def get_message(self, text_data):
        match = MultiplayerMatch.objects.get(pk=self.match_id)
        data = match.game_data
        message = {"group": True}
        players = json.loads(data["players"])
        if text_data["action"] == "request_data":
            message["data"] = data
            message["group"] = False
        elif text_data["action"] == "bid":
            data[self.username+"_bid"] = text_data["bid"]
            data["active"] = after(self.username, players)
            if text_data["re"] == "1":
                if data["re_1"]:
                    data["re_2"] = self.username
                else:
                    data["re_1"] = self.username
            message["data"] = {
                'action': 'bid',
                'username': self.username,
                'bid': text_data['bid'],
                'active': data["active"]
            }
            if data[data["active"]+"_bid"] or text_data["bid"] not in ["healthy", "marriage"]:
                solos = []
                for player in cycle_slice(players.index(data["started"]), players):
                    if data[player+"_bid"] != "healthy":
                        solos.append([player, data[player+"_bid"]])
                if solos:
                    if len(solos) > 1:
                        solos = [solo for solo in solos if solo[1] != "marriage"]
                    player, game_type = solos[0]
                    data["solist"] = player
                    data["game_type"] = game_type
                    data["re_1"] = ""
                    data["re_2"] = ""
                    if game_type != "marriage":
                        data["active"] = player
                        message["data"]["active"] = player
                else:
                    data["game_type"] = "diamonds"
                    message["data"]["game_type"] = "diamonds"
                message["data"]["re_1"] = data["re_1"]
                message["data"]["re_2"] = data["re_2"]
                message["data"]["solist"] = data["solist"]
                message["data"]["game_type"] = data["game_type"]
                message["data"]["mode"] = "playing"
                data["mode"] = "playing"
        elif text_data["action"] == "play":
            handle_play("doko", data, text_data, self.username, message, match)
        elif text_data["action"] == "value":
            if text_data["who"] == "re":
                data["re_value"] = text_data["value"]
            else:
                data["contra_value"] = text_data["value"]
            data["value_ncards"] = text_data["value_ncards"]
            message["data"] = {
                "action": "value",
                "username": self.username,
                "value": text_data["value"],
                "who": text_data["who"],
                "value_ncards": data["value_ncards"]
            }
        match.save()
        return message
