from django.db import models
from activity.models import Activity
from account.models import User
from django.contrib.postgres.fields import HStoreField
from django.shortcuts import reverse
import uuid
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import create_deck
from django.utils.translation import gettext_lazy as _
import json
from multiplayer.utils import change


class MultiplayerMatch(models.Model):
    activity = models.ForeignKey(Activity, related_name='multiplayer_matches', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='multiplayer_matches')
    member_limit = models.PositiveSmallIntegerField()
    member_positions = HStoreField(default=dict)
    game_data = HStoreField(default=dict)
    channel_group_name = models.UUIDField(default=uuid.uuid4)
    in_progress = models.BooleanField(default=False)
    
    @staticmethod
    def match_list_for(activity_id):
        matches = MultiplayerMatch.objects.filter(activity__id=activity_id)
        return [(match.id, [user.username for user in match.members.all()], match.member_limit) for match in matches if not match.is_full()]

    def get_absolute_url(self):
        return reverse('multiplayer:match', args=[self.id])
        
    def lobby_url(self, request=None):
        if request:
            return request.build_absolute_uri(f'/multiplayer/lobby/{self.activity.name}/')
        else:
            return f'/multiplayer/lobby/{self.activity.name}/'
        
    def is_full(self):
        return self.members.all().count() == self.member_limit
        
    def get_position_of(self, member):
        for k, v in self.member_positions.items():
            if v == str(member.id):
                return k
        return None
        
    def add_first_member(self, member):
        for i in range(1, self.member_limit+1):
            self.member_positions[str(i)] = None
        self.member_positions['1'] = str(member.id)
        self.save()
        self.members.add(member)
        
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
        if self.in_progress:
            self.in_progress = False
            self.save()
            if redirect_to_lobby:
                url = self.lobby_url()
            else:
                url = self.get_absolute_url()
            self.broadcast_data({
                'action': 'abort',
                'url': url
            })
            
    def member_list(self):
        result = [f"{u} " for u in self.members.all()]
        for i in range(self.member_limit-self.members.all().count()):
            result.append(_("FREI") + " ")
        return result
        
    def start(self):
        self.game_data = {"type": "multiplayer", "action": "load_data", "game_number": "-1"}
        if self.activity.name == _("Durak"):
            self.start_durak()
        elif self.activity.name == _("Skat"):
            self.start_skat()
        elif self.activity.name == _("Doppelkopf"):
            self.start_doppelkopf()
        if not self.in_progress:
            players = json.loads(self.game_data["players"])
            self.game_data["started"] = players[0]
            for player in players:
                self.game_data[player+"_points"] = "0"
        self.in_progress = True
        self.save()
            
    def create_players(self, n, *deck):
        deck = create_deck(*deck)
        players = []
        for i in range(self.member_limit):
            user = User.objects.get(pk=self.member_positions[str(i+1)])
            players.append(user.username)
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
        players, deck = self.create_players(11, "9", "9", "10", "10", "A", "A", "J", "J", "K", "K", "Q", "Q")
        self.game_data["game_type"] = ""
        self.game_data["declarations"] = ""
        self.game_data["mode"] = "bidding"
        self.game_data["re_1"] = ""
        self.game_data["re_2"] = ""
        self.game_data["active"] = players[1]
        self.game_data["trick"] = json.dumps([])
        for player in players:
            self.game_data[player+"_tricks"] = json.dumps([])
            self.game_data[player+"_bid"] = ""
        change(self.game_data, "game_number", 1)
        
