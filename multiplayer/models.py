from django.db import models
from activity.models import Activity
from account.models import User
from django.contrib.postgres.fields import HStoreField
from django.shortcuts import reverse
import uuid
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import after, create_deck, determine_dealer
from django.utils.translation import gettext_lazy as _, gettext as __
import json
from multiplayer.utils import change
from shared.shared import log
from django.contrib.contenttypes.models import ContentType
import random
from datetime import datetime, timedelta


class MultiplayerMatch(models.Model):
    activity = models.ForeignKey(Activity, related_name='multiplayer_matches', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='multiplayer_matches')
    member_limit = models.PositiveSmallIntegerField()
    member_positions = HStoreField(default=dict, blank=True)
    game_data = HStoreField(default=dict, blank=True)
    channel_group_name = models.UUIDField(default=uuid.uuid4)
    in_progress = models.BooleanField(default=False)
    admin = models.ForeignKey(User, related_name='admin_matches', on_delete=models.CASCADE)
    
    def __str__(self):
        return self.activity.name+__('-Match')
    
    @staticmethod
    def last():
        return MultiplayerMatch.objects.last()
    
    @staticmethod
    def match_list_for(activity_id):
        matches = MultiplayerMatch.objects.filter(activity__id=activity_id)
        return [(match.id, [v for k, v in match.member_positions.items() if v], match.member_limit) for match in matches if not match.is_full()]
        
    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='multiplayer', model='multiplayermatch')
        
    def add_member(self, user):
        for k, v in self.member_positions.items():
            if not v:
                self.member_positions[k] = user.username
                self.save()
                break
        self.broadcast_data(
            {
                'action': 'members_changed',
                "match_id": self.id,
                "info": "joined",
                "position": k,
                "username": user.username,
                'id': user.id
            }, 
            direct=True
        )
        self.members.add(user)
        
    def remove_member(self, member):
        for k, v in self.member_positions.items():
            if str(v) == member.username:
                self.member_positions[k] = ""
                self.save()
                break
        if self.in_progress:
            self.abort()
        else:
            self.broadcast_data(
                {
                    'action': 'members_changed',
                    "match_id": self.id,
                    "info": "left",
                    "position": k,
                    "username": member.username,
                    'id': member.id
                },
                direct=True
            )
        self.members.remove(member)
        
    def chat_allowed_for(self, user):
        return self.members.filter(pk=user.id).exists()

    def get_absolute_url(self):
        return reverse('multiplayer:match', args=[self.activity.name, self.id])
        
    def lobby_url(self, request=None):
        return self.activity.lobby_url(request)
        
    def is_full(self):
        return self.members.count() == self.member_limit
        
    def get_position_of(self, member):
        for k, v in self.member_positions.items():
            if v == member.username:
                return k
        return None
        
    def init_positions(self):
        for i in range(2, self.member_limit+1):
            self.member_positions[str(i)] = ""
        self.member_positions['1'] = self.admin.username
        self.save()
        
    def broadcast_data(self, data, direct=False):
        channel_layer = get_channel_layer()
        data["type"] = "multiplayer"
        if direct:
            for user in self.members.all():
                async_to_sync(channel_layer.group_send)(
                    user.channel_group_name,
                    data
                )
        else:
            async_to_sync(channel_layer.group_send)(
                f"match-{self.id}",
                data
            )
            
    def abort(self, redirect_to_lobby=False):
        if redirect_to_lobby:
            url = self.lobby_url()
        else:
            url = self.get_absolute_url()
        if self.in_progress:
            self.broadcast_data({
                'action': 'abort',
                'url': url
            })
            self.in_progress = False
            self.save()
        else:
            self.broadcast_data({
                'action': 'members_changed',
                'info': 'abort',
                'url': url,
                'match_id': self.id
            }, direct=True)
        
    def start(self):
        self.in_progress = False
        self.game_data = {"type": "multiplayer", "action": "load_data", "game_number": "-1"}
        if self.activity.german_name == "Durak":
            self.start_durak()
            players = json.loads(self.game_data['players'])
            self.game_data["attacking"] = random.choice(players)
            self.game_data["defending"] = after(self.game_data['attacking'], players)
        elif self.activity.german_name == "Skat":
            self.start_skat()
        elif self.activity.german_name == "Doppelkopf":
            self.start_doppelkopf()
        elif self.activity.german_name == 'Poker':
            self.start_poker()
        # if self.in_progress return? TODO
        players = json.loads(self.game_data["players"])
        self.game_data["started"] = players[0]
        if self.activity.german_name != 'Poker':
            for player in players:
                self.game_data[player+"_points"] = "0"
        self.in_progress = True
        self.save()
        self.broadcast_data(
                {
                    'action': 'members_changed',
                    "match_id": self.id,
                    "info": "start"
                }, 
                direct=True
            )
            
    def create_players(self, n, *deck):
        deck = create_deck(*deck)
        if 'players' not in self.game_data:
            players = []
            for k, v in self.member_positions.items():
                players.append(v)
            self.game_data["players"] = json.dumps(players)
        else:
            players = json.loads(self.game_data['players'])
        for player in players:
            self.game_data[player] = json.dumps(deck[:n])
            deck = deck[n:]
            if len(deck) < n:
                break
        self.game_data["deck"] = json.dumps(deck)
        return players, deck
            
    def start_skat(self):
        players, _ = self.create_players(10, "7", "8", "9", "10", "J", "Q", "K", "A")
        self.game_data["forehand"] = players[0]
        self.game_data["last_bid"] = ""
        self.game_data["highest_bid"] = ""
        self.game_data["more"] = ""
        self.game_data["trick"] = json.dumps([])
        self.game_data["factor"] = ""
        for player in players:
            self.game_data[player+"_tricks"] = json.dumps([])
            self.game_data[player+"_bid"] = ""
        self.game_data["active"] = players[1]
        self.game_data["solist"] = ""
        self.game_data["game_type"] = ""
        self.game_data["declarations"] = ""
        self.game_data["passed"] = ""
        self.game_data["last_trick"] = json.dumps([])
        # bidding, taking, putting, declaring, playing
        self.game_data["mode"] = "bidding"
        change(self.game_data, "game_number", 1)
        

    def start_durak(self):
        log('-------------Starting Durak round-------------')
        players, deck = self.create_players(6, "10", "J", "Q", "K", "A")
        self.game_data["trump"] = deck[-1][-1]
        self.game_data["stacks"] = json.dumps([])
        self.game_data["done_list"] = json.dumps([])
        self.game_data["taking"] = ""
        self.game_data["first"] = "" # first without cards
        change(self.game_data, "game_number", 1)
        
        
    def start_doppelkopf(self):
        players, _ = self.create_players(12, "9", "9", "10", "10", "A", "A", "J", "J", "K", "K", "Q", "Q")
        self.game_data["game_type"] = ""
        self.game_data["re_value"] = ""
        self.game_data["contra_value"] = ""
        self.game_data["re_extra"] = "0"
        self.game_data["contra_extra"] = "0"
        self.game_data["mode"] = "bidding"
        self.game_data["re_1"] = ""
        self.game_data["re_2"] = ""
        self.game_data["solist"] = ""
        self.game_data["trick"] = json.dumps([])
        self.game_data["m_show"] = "0"
        self.game_data["value_ncards"] = "0"
        self.game_data["active"] = players[0]
        self.game_data["last_trick"] = json.dumps([])
        for player in players:
            self.game_data[player+"_tricks"] = json.dumps([])
            self.game_data[player+"_bid"] = ""
        change(self.game_data, "game_number", 1)
        
    def start_poker(self):
        players, deck = self.create_players(2, "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
        self.game_data['deck'] = json.dumps(deck[:5])
        self.game_data['cards'] = json.dumps([])
        self.game_data['show_list'] = json.dumps([])
        if not self.in_progress:
            self.game_data['blinds'] = json.dumps([[10, 20], [20, 40], [30, 60], [50, 100], [100, 200], [150, 300], [200, 400], [400, 800], [800, 1600]])
            self.game_data['dealer'] = ''
            self.game_data['blind_duration'] = 20
            self.game_data['blind_time'] = (timezone.now()+timedelta(minutes=int(self.game_data['blind_duration']))).isoformat()
            self.game_data['blind_level'] = 0
            self.game_data['alive'] = json.dumps(players)
            for player in players:
                self.game_data[player+'_stack'] = 20*100
                self.game_data[player+'_bet'] = 0
        alive = json.loads(self.game_data['alive'])
        alive = [user for user in alive if int(self.game_data[user+'_stack']) > 0]
        for user in alive:
            self.game_data[user+'_bet'] = 0
        self.game_data['alive'] = json.dumps(alive)
        if len(alive) == 1:
            self.game_data['winner'] = alive[0]
            self.delete()
            return
        blinds = [[10, 20], [20, 40], [30, 60], [50, 100], [100, 200], [150, 300], [200, 400], [400, 800], [800, 1600]]
        if int(self.game_data['blind_level']) < len(blinds)-1 and timezone.now() > datetime.fromisoformat(self.game_data['blind_time']):
            change(self.game_data, 'blind_level', 1)
            self.game_data['blind_time'] = (timezone.now()+timedelta(minutes=int(self.game_data['blind_duration']))).isoformat()
        determine_dealer(self.game_data)
        small_blind, big_blind = blinds[int(self.game_data['blind_level'])]
        change(self.game_data, self.game_data['small_blind']+'_stack', -small_blind, guard_zero=True)
        self.game_data[self.game_data['small_blind']+'_bet'] = small_blind
        change(self.game_data, self.game_data['big_blind']+'_stack', -big_blind, guard_zero=True)
        self.game_data[self.game_data['big_blind']+'_bet'] = big_blind
        self.game_data['pot'] = small_blind+big_blind
        self.game_data['highest_bet_user'] = ""
        self.game_data['highest_bet_value'] = big_blind
        self.game_data['previous_raise'] = big_blind
        change(self.game_data, 'game_number', 1)
        self.game_data['active'] = after(self.game_data['big_blind'], players)
