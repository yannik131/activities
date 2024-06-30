import logging

from django.db import models
from activity.models import Activity
from account.models import User
from django.contrib.postgres.fields import HStoreField
from django.shortcuts import reverse
import uuid
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import after, create_deck, determine_dealer, set_blinds
from django.utils.translation import gettext_lazy as _, gettext as __
import json
from multiplayer.utils import change
from shared.shared import log
from django.contrib.contenttypes.models import ContentType
import random
from datetime import datetime, time, timedelta
from redis import StrictRedis
conn = StrictRedis(host="localhost", port=6655)
import redis_lock
from datetime import timedelta

logger = logging.getLogger('django')

class MultiplayerMatch(models.Model):
    MAX_INSTANCES = 5
    RUNNING_LIFESPAN = timedelta(days=7)
    IDLE_LIFESPAN = timedelta(hours=1)
    created = models.DateTimeField(default=timezone.now)
    activity = models.ForeignKey(Activity, related_name='multiplayer_matches', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='multiplayer_matches')
    member_limit = models.PositiveSmallIntegerField(blank=True)
    member_positions = HStoreField(default=dict, blank=True)
    game_data = HStoreField(default=dict, blank=True)
    in_progress = models.BooleanField(default=False)
    admin = models.ForeignKey(User, related_name='admin_matches', on_delete=models.CASCADE)
    options = HStoreField(default=dict, blank=True)
    over = models.BooleanField(default=False)
    invisible = models.BooleanField(default=False)
    action_strings = {
        'is_full': _('ist voll')
    }
    
    class Meta:
        ordering = ['-created']
        
    @property
    def delete_date(self):
        if self.in_progress:
            return self.created+MultiplayerMatch.RUNNING_LIFESPAN
        else:
            return self.created+MultiplayerMatch.IDLE_LIFESPAN
    
    @property
    def get_image(self):
        return self.activity.image
        
    @property
    def start_member_limit(self):
        name = self.activity.german_name
        if name in ['Poker', 'Durak', 'Stiche raten']:
            return 2
        else:
            return self.member_limit
            
    @staticmethod
    def running_lifetime_days():
        return MultiplayerMatch.RUNNING_LIFESPAN.days
        
    @staticmethod
    def idle_lifetime_minutes():
        return int(MultiplayerMatch.IDLE_LIFESPAN.seconds/60)
    
    def __str__(self):
        return self.activity.name+__('-Match')
        
    def verbose(self):
        return self.__str__()
    
    @staticmethod
    def last():
        return MultiplayerMatch.objects.last()
    
    @staticmethod
    def match_list_for(activity_id):
        matches = MultiplayerMatch.objects.filter(activity__id=activity_id, invisible=False)
        return [(match.id, [v for k, v in match.member_positions.items() if v], match.member_limit, match.created.isoformat()) for match in matches if not (match.is_full() or match.in_progress)]
        
    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='multiplayer', model='multiplayermatch')
        
    def add_member(self, user):
        with redis_lock.Lock(conn, str(self.id)):
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
        with redis_lock.Lock(conn, str(self.id)):
            for k, v in self.member_positions.items():
                if v == member.username:
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
        
    def can_start(self):
        return self.members.count() >= self.start_member_limit
        
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
        
    def get_member_names(self):
        return [v for k, v in self.member_positions.items() if v]
    
    def trim_positions(self):
        positions = dict()
        for i, username in enumerate(self.member_positions.values(), start=1):
            if username:
                positions[str(i)] = username
        self.member_positions = positions
        self.member_limit = len(positions)
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
            self.created = timezone.now()
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
        self.trim_positions()
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
        elif self.activity.german_name == 'Stiche raten':
            self.start_guess_the_tricks()
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
            random.shuffle(players)
            self.game_data["players"] = json.dumps(players)
        else:
            players = json.loads(self.game_data['players'])
        for player in players:
            self.game_data[player] = json.dumps(deck[:n])
            if self.activity.german_name in ["Doppelkopf", "Skat", "Stiche raten"]:
                self.game_data[player + "_initial_hand"] = json.dumps(deck[:n])
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
        self.game_data["skat"] = self.game_data["deck"]
        # bidding, taking, putting, declaring, playing
        self.game_data["mode"] = "bidding"
        change(self.game_data, "game_number", 1)
        

    def start_durak(self):
        if self.member_limit <= 3:
            players, deck = self.create_players(6, "7", "8", "9", "10", "J", "Q", "K", "A")
        elif self.member_limit == 4:
            players, deck = self.create_players(6, "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
        else:
            players, deck = self.create_players(6, "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A")
        self.game_data["trump"] = deck[-1][-1]
        self.game_data["stacks"] = json.dumps([])
        self.game_data["done_list"] = json.dumps([])
        self.game_data["taking"] = ""
        self.game_data["first"] = "" # first without cards
        change(self.game_data, "game_number", 1)
        
        
    def start_doppelkopf(self):
        if "players" not in self.game_data: #game is being created for the first time
            self.game_data["played_solo"] = json.dumps({})
            self.game_data["round_count"] = self.options['round_count']
        if self.options['without_nines'] == 'True':
            players, _ = self.create_players(10, "10", "10", "A", "A", "J", "J", "K", "K", "Q", "Q")
            self.game_data['without_nines'] = '1'
        else:
            players, _ = self.create_players(12, "9", "9", "10", "10", "A", "A", "J", "J", "K", "K", "Q", "Q")
            self.game_data['without_nines'] = '0'
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
        self.game_data["tricks"] = json.dumps([]) #(trick, winner, index of who started)
        self.game_data["mandatory_solo"] = ""
        self.game_data["re_bids"] = json.dumps(dict())
        self.game_data["contra_bids"] = json.dumps(dict())
        for player in players:
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
            self.game_data['blind_duration'] = self.options['blind_duration']
            self.game_data['blind_time'] = (timezone.now()+timedelta(minutes=int(self.game_data['blind_duration']))).isoformat()
            self.game_data['blind_level'] = 0
            self.game_data['alive'] = json.dumps(players)
            for player in players:
                self.game_data[player+'_stack'] = 20*100
                self.game_data[player+'_bet'] = 0
        alive = json.loads(self.game_data['alive'])
        alive = [user for user in alive if int(self.game_data[user+'_stack']) > 0]
        for user in players:
            self.game_data[user+'_bet'] = 0
        self.game_data['alive'] = json.dumps(alive)
        if len(alive) == 1:
            self.game_data['winner'] = alive[0]
            self.over = True
            self.created = timezone.now()
            return
        blinds = [[10, 20], [20, 40], [30, 60], [50, 100], [100, 200], [150, 300], [200, 400], [400, 800], [800, 1600]]
        if int(self.game_data['blind_level']) < len(blinds)-1 and timezone.now() > datetime.fromisoformat(self.game_data['blind_time']):
            change(self.game_data, 'blind_level', 1)
            self.game_data['blind_time'] = (timezone.now()+timedelta(minutes=int(self.game_data['blind_duration']))).isoformat()
        determine_dealer(self.game_data)
        set_blinds(self.game_data, blinds)
        change(self.game_data, 'game_number', 1)
        self.game_data['active'] = after(self.game_data['big_blind'], alive)
        
    def start_guess_the_tricks(self):
        change(self.game_data, 'game_number', 1)
        n_cards = int(self.game_data['game_number']) + 1
        players, _ = self.create_players(n_cards, "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "A")
        for user in players:
            self.game_data[user + "_guess"] = None
            self.game_data[user + "_tricks"] = 0
        self.game_data['active'] = players[0]
        self.game_data['mode'] = 'guessing'
        self.game_data['trick'] = json.dumps([])
        
