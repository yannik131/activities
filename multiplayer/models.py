from django.db import models
from activity.models import Activity
from account.models import User
from django.contrib.postgres.fields import HStoreField
from django.shortcuts import reverse
import uuid
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import after, create_deck
from django.utils.translation import gettext_lazy as _
import json
from multiplayer.utils import change
from shared.shared import log


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
        return self.activity.name
    
    @staticmethod
    def last():
        return MultiplayerMatch.objects.all().last()
    
    @staticmethod
    def match_list_for(activity_id):
        matches = MultiplayerMatch.objects.filter(activity__id=activity_id)
        return [(match.id, [v for k, v in match.member_positions.items() if v], match.member_limit) for match in matches if not match.is_full()]
        
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
        self.game_data = {"type": "multiplayer", "action": "load_data", "game_number": "-1"}
        if self.activity.name == _("Durak"):
            self.start_durak()
        elif self.activity.name == _("Skat"):
            self.start_skat()
        elif self.activity.name == _("Doppelkopf"):
            self.start_doppelkopf()
        # if self.in_progress return? TODO
        players = json.loads(self.game_data["players"])
        self.game_data["started"] = players[0]
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
        players = []
        for k, v in self.member_positions.items():
            players.append(v)
        self.game_data["players"] = json.dumps(players)
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
        players, deck = self.create_players(6, "6", "7", "8", "9", "10", "J", "Q", "K", "A")
        self.game_data["trump"] = deck[-1][-1]
        self.game_data["attacking"] = players[0]
        self.game_data["defending"] = players[1]
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
        
