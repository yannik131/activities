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
        try:
            match = MultiplayerMatch.objects.get(pk=self.match_id)
        except:
            log(self.username, "requested invalid match with id", self.match_id)
            return dict()
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
                        data["attacking"] = after(data["started"], players)
                        data["defending"] = after(data["attacking"], players)
                    message["data"] = match.game_data
                    message["data"]["summary"] = summary
                    message["data"]["game_number"] = data["game_number"]
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
            players = json.loads(data["players"])
            players = cycle_slice(players.index(data["forehand"]), players)
            data["trick"] = text_data["trick"]
            trick = json.loads(data["trick"])
            data[data["active"]] = text_data["hand"]
            data["active"] = after(self.username, players)
            message["data"] = {
                "action": "play",
                "trick": data["trick"],
                "username": self.username,
                "active": data["active"]
            }
            if len(trick) == 3:
                winner = players[int(text_data["index"])]
                tricks = json.loads(data[winner+"_tricks"])
                tricks.append(trick)
                data[winner+"_tricks"] = json.dumps(tricks)
                data["forehand"] = winner
                data["active"] = winner
                data["trick"] = json.dumps([])
                message["data"]["clear"] = "1"
                message["data"]["forehand"] = winner
                message["data"]["active"] = winner
                ouvert_null_lost = (data["game_type"] == "n" and data["solist"] == winner) or (("o" in data["declarations"] or "b" in data["declarations"]) and data["solist"] != winner)
                if not json.loads(data[data["active"]]) or ouvert_null_lost:
                    players = json.loads(data["players"])
                    result, winner_points, game_value = determine_winner(data)
                    points_summary = give_skat_points(data, players, result, game_value)
                    message["data"]["result"] = result
                    if winner_points:
                        message["data"]["points"] = winner_points
                    message["data"]["summary"] = points_summary
                    data["summary"] = points_summary
                    message["data"]["game_number"] = data["game_number"]
                    match.start_skat()
                    starting = after(data["started"], players)
                    match.game_data["started"] = starting
                    match.game_data["forehand"] = starting
                    match.game_data["active"] = after(starting, players)
                    message["data"]["round"] = match.game_data
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
                match.start()
                message["data"] = match.game_data
        match.save()
        return message

class AudioReceiveConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        
        async_to_sync(self.channel_layer.group_add)(
            f"audio-receive-{self.match_id}",
            self.channel_name
        )
        
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f"audio-receive-{self.match_id}",
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        text_data = dict()
        text_data["type"] = "audio_message"
        text_data["sender"] = self.username
        text_data["bytes_data"] = bytes_data
        async_to_sync(self.channel_layer.group_send)(
            f"audio-send-{self.match_id}",
            text_data
        )
            
class AudioSendConsumer(WebsocketConsumer):
    def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        
        async_to_sync(self.channel_layer.group_add)(
            f"audio-send-{self.match_id}",
            self.channel_name
        )
        
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            f"audio-send-{self.match_id}",
            self.channel_name
        )

    def audio_message(self, event):
        if event["sender"] != self.username:
            self.send(bytes_data=event["bytes_data"])
            
"""
class AudioReceiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        log("connected: ", self.username)
        
        await self.channel_layer.group_add(
            f"audio-receive-{self.match_id}",
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"audio-receive-{self.match_id}",
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        text_data = dict()
        text_data["type"] = "audio_message"
        text_data["sender"] = self.username
        text_data["bytes_data"] = bytes_data
        await self.channel_layer.group_send(
            f"audio-send-{self.match_id}",
            text_data
        )
            
class AudioSendConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        
        await self.channel_layer.group_add(
            f"audio-send-{self.match_id}",
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            f"audio-send-{self.match_id}",
            self.channel_name
        )

    async def audio_message(self, event):
        if event["sender"] != self.username:
            await self.send(bytes_data=event["bytes_data"])
"""
    