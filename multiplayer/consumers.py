import json
from channels.generic.websocket import WebsocketConsumer
from multiplayer.models import MultiplayerMatch
from multiplayer.utils import *
from redis import StrictRedis
conn = StrictRedis(host="localhost", port=6655)
import redis_lock
from asgiref.sync import async_to_sync
from shared.shared import log
from account.models import User
from . import utils


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.username = self.scope['url_route']['kwargs']['username']
        key = self.scope['url_route']['kwargs']['key']
        if User.objects.get(username=self.username).ws_key != key:
            return
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        if MultiplayerMatch.objects.filter(pk=self.match_id).exists():
            async_to_sync(self.channel_layer.group_add)(
                f"match-{self.match_id}",
                self.channel_name
            )
            self.german_name = MultiplayerMatch.objects.get(pk=self.match_id).activity.german_name
            
            self.accept()

    def disconnect(self, code):
        if not hasattr(self, 'match_id'):
            return
        async_to_sync(self.channel_layer.group_discard)(
            f"match-{self.match_id}",
            self.channel_name
        )
    
    def multiplayer(self, event):
        self.send(text_data=json.dumps(event))
        
    def receive(self, text_data=None):
        text_data = json.loads(text_data)
        if text_data['action'] == 'request_data':
            match = MultiplayerMatch.objects.get(pk=self.match_id)
            if match.activity.german_name == "Doppelkopf":
                utils.clean_doko_data(match.game_data, self.username)
            self.multiplayer(match.game_data)
            return
            
        with redis_lock.Lock(conn, self.match_id):
            match = MultiplayerMatch.objects.get(pk=self.match_id)
            message = dict()
            self.handle_move(text_data, match.game_data, match, message)
            match.save()
            if not "data" in message:
                return
            message["data"]["type"] = "multiplayer"
            async_to_sync(self.channel_layer.group_send)(
                f"match-{self.match_id}",
                message["data"]
            )
                
class DurakConsumer(GameConsumer):
    def handle_move(self, text_data, data, match, message):
        players = json.loads(data["players"])
        if text_data['action'] in ["beating", "attacking"]:
            rejected = refresh_stacks(data, text_data, self.username == data['defending'])
            if not rejected:
                data[self.username] = text_data["hand"]
                if not data["first"] and len(json.loads(text_data["hand"])) == 0:
                    data["first"] = self.username
                if not data["taking"]:
                    data["done_list"] = json.dumps([])
            message["data"] = {
                "username": self.username,
                "action": "play",
                "stacks": data["stacks"],
                "played_cards": text_data["played_cards"],
                "defending": data["defending"],
                "attacking": data["attacking"],
                'rejected': "1" if rejected else "",
                'done_list': data['done_list']
            }
            if text_data['action'] == 'beating':
                message['data']['beating'] = '1'
            if not rejected:
                handle_durak_next_phase(data, match, message, self.username)
        elif text_data['action'] == "done":
            data['done_list'] = json.dumps(list(dict.fromkeys(json.loads(data['done_list'])+[self.username]).keys()))
            message['data'] = {
                'action': 'done',
                'done_list': data['done_list']
            }
            handle_durak_next_phase(data, match, message, self.username)
        elif text_data["action"] == "take":
            data["done_list"] = json.dumps([])
            data["taking"] = self.username
            message["data"] = {
                "action": "take"
            }
            handle_durak_next_phase(data, match, message, self.username)
        elif text_data["action"] == "transfer":
            refresh_stacks(data, text_data, False)
            data[self.username] = text_data["hand"]
            if not data["first"] and len(json.loads(text_data["hand"])) == 0:
                data["first"] = self.username
            data["attacking"] = data["defending"]
            data["defending"] = left_player(data["attacking"], players, data)
            message["data"] = {
                "action": "transfer",
                "attacking": data["attacking"],
                "defending": data["defending"],
                "stacks": data["stacks"],
                "played_cards": text_data["played_cards"],
                "username": self.username
            }
            
class SkatConsumer(GameConsumer):
    def handle_move(self, text_data, data, match, message):
        if text_data["action"] == "play":
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
                set_initial_data(message, data)
                match.start_skat()
                data["started"] = after(data["started"], players)
                data["forehand"] = data["started"]
                data["active"] = after(data["forehand"], players)
                message["data"]["round"] = match.game_data
                message["data"]["players"] = data["players"]

class DoppelkopfConsumer(GameConsumer):
    def handle_move(self, text_data, data, match, message):
        if self.username != data["active"]:
            return
        players = json.loads(data["players"])
        if text_data["action"] == "bid":
            message["data"] = {
                'action': 'bid',
                'username': self.username,
                'bid': text_data['bid'],
                'players': data['players']
            }
            if text_data["bid"] == "poverty":
                message["data"]["summary"] = f"{self.username}: Armut"
                players = json.loads(data["players"])
                for player in players:
                    message["data"][player + "_initial_hand"] = data[player + "_initial_hand"]
                match.start_doppelkopf()
                change(data, "game_number", -1)
                message["data"]["round"] = match.game_data.copy()
                return
            data[self.username+"_bid"] = text_data["bid"]
            data["active"] = after(self.username, players)
            if text_data["re"] == "1":
                if data["re_1"]:
                    data["re_2"] = self.username
                else:
                    data["re_1"] = self.username

            message["data"]['active'] = data["active"]
            bidding_over = bool(data[data["active"]+"_bid"])
            bid_is_solo = text_data["bid"] not in ["healthy", "marriage"]
            played_solo = json.loads(data["played_solo"])

            if bid_is_solo and self.username not in played_solo:
                # mandatory solo
                data["solist"] = self.username
                data["game_type"] = text_data["bid"]
                data["re_1"] = ""
                data["re_2"] = ""
                data["active"] = self.username
                message["data"]["active"] = self.username
            elif bidding_over:
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
                else:
                    data["game_type"] = "diamonds"
                    message["data"]["game_type"] = "diamonds"
            else:
                return

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
                data["re_bids"] = utils.create_json_dict_entry(data["re_bids"], self.username, text_data["value"])
            else:
                data["contra_value"] = text_data["value"]
                data["contra_bids"] = utils.create_json_dict_entry(data["contra_bids"], self.username, text_data["value"])
            data["value_ncards"] = text_data["value_ncards"]
            message["data"] = {
                "action": "value",
                "username": self.username,
                "value": text_data["value"],
                "who": text_data["who"],
                "value_ncards": data["value_ncards"],
                "re_bids": data["re_bids"],
                "contra_bids": data["contra_bids"]
            }

class PokerConsumer(GameConsumer):
    def handle_move(self, text_data, data, match, message):
        if self.username not in json.loads(data['alive']):
            return
        if text_data['action'] == 'fold':
            data[self.username+'_bet'] = 'fold'
            message['data'] = {
                'action': 'fold',
                'user': self.username
            }
            remaining_players = no_fold(data)
            if len(remaining_players) == 1:
                change(data, remaining_players[0]+'_stack', int(data['pot']))
                message['data']['pot'] = data['pot']
                match.start_poker()
                message['data']['new_game_data'] = match.game_data
                message['data']['winner'] = remaining_players[0]
                return
        elif text_data['action'] == 'raise':
            change(data, self.username+'_bet', int(text_data['to_pay']))
            data['highest_bet_value'] = data[self.username+'_bet']
            data['previous_raise'] = int(text_data['value'])
            change(data, self.username+'_stack', -int(text_data['to_pay']))
            change(data, 'pot', int(text_data['to_pay']))
            data['highest_bet_user'] = self.username
            
            message['data'] = {
                'action': 'raise',
                'user': self.username,
                'value': text_data['value'],
                'stack': data[self.username+'_stack'],
                'pot': data['pot']
            }
        elif text_data['action'] == 'call':
            change(data, self.username+'_stack', -int(text_data['value']))
            change(data, self.username+'_bet', int(text_data['value']))
            change(data, 'pot', int(text_data['value']))
            
            message['data'] = {
                'action': 'call',
                'user': self.username,
                'stack': data[self.username+'_stack'],
                'pot': data['pot']
            }
        elif text_data['action'] == 'check':
            message['data'] = {
                'action': 'check',
                'user': self.username,
                'stack': data[self.username+'_stack']
            }
        elif text_data['action'] == 'show':
            if text_data['value'] == '1':
                show_list = json.loads(data['show_list'])
                show_list.append(self.username)
                data['show_list'] = json.dumps(show_list)
                message['data'] = {
                    'user': self.username,
                    'action': 'show',
                    'hand': data[self.username]
                }
            else:
                message['data'] = {
                    'action': 'show',
                }
            data['active'] = after(data['active'], no_fold(data))
            message['data']['active'] = data['active']
            if data['active'] == determine_forced_player(data):
                summary = determine_winners_poker(data)
                match.start_poker()
                message['data']['new_game_data'] = match.game_data
                message['data']['summary'] = summary
                message['data']['active'] = ''
            return
        
        next_round_number = get_next_round_number(data, text_data['action'], data['active'])
        if next_round_number:
            if next_round_number == 5:
                forced_player = determine_forced_player(data)
                message['data']['forced'] = forced_player
                show_list = json.loads(data['show_list'])
                show_list.append(forced_player)
                data['show_list'] = json.dumps(show_list)
                data['active'] = after(forced_player, no_fold(data))
                message['data']['hand'] = data[forced_player]
            else:
                start_round(data)
                message['data']['cards'] = data['cards']
                message['data']['new_round'] = "1"
        else:
            if text_data['action'] == 'fold':
                players = json.loads(data['alive'])
                active = after(data['active'], players)
                while data[active+'_bet'] == 'fold':
                    active = after(active, players)
                data['active'] = active
            else:
                data['active'] = after(data['active'], no_fold(data))
        
        message['data']['active'] = data['active']
        
    def clean(self, data):
        del data['deck']
        for player in json.loads(data['alive']):
            if player != self.username and data[player+'_bet'] != 'show':
                del data[player]
        
    def multiplayer(self, event):
        """
        #TODO: figure security out, this method won't work, because the event variable will not be deepcopied for every user. maybe deepcopying?
        if 'deck' in event:
            self.clean(event)
        elif 'new_game_data' in event:
            if 'deck' in event['new_game_data']:
                self.clean(event['new_game_data'])
        """
        self.send(text_data=json.dumps(event))
        
class GuessTheTricksConsumer(GameConsumer):
    def handle_move(self, text_data, data, match, message):
        players = json.loads(data["players"])
        if text_data['action'] == 'guess':
            data[self.username + "_guess"] = text_data['guess']
            data["active"] = after(data["active"], players)
            if data[data['active'] + '_guess'] is not None:
                data['mode'] = 'playing'
            message['data'] = {
                'action': 'guess', 
                'username': self.username, 
                'guess': text_data['guess'],
                'active': data['active'],
                'mode': data['mode']
            }
        elif text_data['action'] == 'play':
            players = cycle_slice(players.index(after(data["active"], players)), players)
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
            
            if "index" in text_data:
                winner = players[int(text_data["index"])]
                data["last_trick"] = json.dumps(trick)
                change(data, winner + "_tricks", 1)
                
                data["active"] = winner
                data["trick"] = json.dumps([])
                message["data"]["next_trick"] = 1
                message["data"]["active"] = winner
                message["data"][winner + "_tricks"] = data[winner + "_tricks"]
                
                if not json.loads(data[data["active"]]):
                    utils.calculate_guess_the_tricks_score(data)
                    if len(players) * (int(data['game_number']) + 1) > 11 * 4:
                        # Currently only the cards 2-10 and J and A are used. So there are 4 * 11 cards in total
                        message['data']['game_over'] = True
                        data['game_over'] = True
                    else:
                        match.start_guess_the_tricks()
                    del message['data']['next_trick']
                    message['data']['last_scores'] = json.dumps({player: data[player + '_last_score'] for player in players})
                    message['data']['points'] = json.dumps({player: data[player + '_points'] for player in players})
                    message['data']['next_round'] = 1
                    message["data"]["round"] = match.game_data.copy()
        elif text_data['action'] == 'set_trump_suit':
            data['trump_suit_wizard'] = text_data['trump_suit']
            message['data'] = {
                'action': 'set_trump_suit',
                'trump_suit': text_data['trump_suit']
            }