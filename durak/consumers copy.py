from concurrent.futures import thread
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from chat.models import ChatRoom, ChatLogEntry, ChatCheck
from channels.db import database_sync_to_async as db_sync
from multiplayer.models import MultiplayerMatch
from multiplayer.utils import before, deal_cards, left_player, player_with_cards
from shared.shared import log
from django_pglocks import advisory_lock
from channels.layers import get_channel_layer
from account.models import User
from redis import StrictRedis
conn = StrictRedis()
import redis_lock


class DurakConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.username = self.scope['url_route']['kwargs']['username']
        self.channel_group_name = self.scope['url_rout']['kwargs']['group_name']

        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.channel_group_name,
            self.channel_name
        )
        
    def get_match(self, match_id):
        return MultiplayerMatch.objects.get(pk=match_id)
    
    def get_attr(self, property):
        return getattr(self.match, property)
        
    def call_attr(self, method, *args):
        getattr(self.match, method)(*args)
        
    def get_message(self, text_data):
        with 
            log(self.username, "entered function with action", text_data["action"])
            match = MultiplayerMatch.objects.get(pk=text_data['match_id'])
            data = match.game_data
            players = json.loads(data["players"])
            message = {"group": True}
            if text_data['action'] == "request_data":
                if not match.in_progress:
                    match.start()
                    message["data"] = data
                else:
                    message["data"] = data
                    message["group"] = False
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
                #log(self.username, "done received", done_list)
                if(str(self.username) not in done_list):
                    done_list.append(str(self.username))
                    #log(self.username, "adding to list")
                
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
                    else:
                        if data["defending"]:
                            if json.loads(data[data["defending"]]):
                                data["attacking"] = data["defending"]
                            else:
                                data["attacking"] = left_player(data["defending"], players, data)
                        else:
                            data["attacking"] = None
                    deal_cards(data, players)
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
                    "defending": data["defending"],
                    "stacks": data["stacks"]
                }
            match.save()
            done_list = json.loads(match.game_data["done_list"])
            #if text_data["action"] == "done":
            #    log(self.username, "result:", done_list)
            log(self.username, "done with all")
            return message

    async def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        log(self.username, "received: ", text_data["action"])
        message = await db_sync(self.get_message)(text_data)
        if not "data" in message:
            return
        message["data"]["type"] = "multiplayer"
        if message["group"]:
            await self.channel_layer.group_send(
                self.room_group_name,
                message["data"]
            )
        else:
            await self.send(text_data=json.dumps(message["data"]))
            
        
    async def multiplayer(self, event):
        await self.send(text_data=json.dumps(event))
