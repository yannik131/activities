from django.db import models
from activity.models import Activity
from account.models import User
from django.contrib.postgres.fields import HStoreField
from django.shortcuts import reverse
import uuid
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import create_deck
import json


class MultiplayerMatch(models.Model):
    activity = models.ForeignKey(Activity, related_name='multiplayer_matches', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='multiplayer_matches')
    member_limit = models.PositiveSmallIntegerField()
    member_positions = HStoreField(default=dict)
    game_data = HStoreField(default=dict)
    channel_group_name = models.UUIDField(default=uuid.uuid4)
    in_progress = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse('multiplayer:match', args=[self.id])
        
    def lobby_url(self, request):
        return request.build_absolute_uri(f'/multiplayer/lobby/{self.activity.name}/')
        
    def is_ready(self):
        return self.member_limit == self.members.all().count()
        
    def is_full(self):
        return self.members.all().count() == self.member_limit
        
    def get_position_of(self, member):
        for k, v in self.member_positions.items():
            if v == str(member.id):
                return k
        return None
        
    def broadcast_data(self, data):
        channel_layer = get_channel_layer()
        data["type"] = "multiplayer"
        for member in self.members.all():
            async_to_sync(channel_layer.group_send)(
                member.channel_group_name,
                data
            )

    def start(self):
        self.in_progress = True
        self.game_data = dict()
        deck = create_deck("8", "9", "K", "Q", "A", "J")
        self.game_data["trump"] = deck[-1][-1]
        self.game_data["type"] = "multiplayer"
        self.game_data["action"] = "load_data"
        players = []
        for i in range(self.member_limit):
            user = User.objects.get(pk=self.member_positions[str(i+1)])
            players.append(user.username)
        self.game_data["players"] = json.dumps(players)
        for player in players:
            self.game_data[player] = json.dumps(deck[:6])
            deck = deck[6:]
        self.game_data["deck"] = json.dumps(deck)
        self.game_data["first_attacker"] = players[0]
        self.game_data["attacking"] = players[0]
        self.game_data["defending"] = players[1]
        self.game_data["stacks"] = json.dumps([])
        self.game_data["done_list"] = json.dumps([])
        self.game_data["taking"] = ""
        self.save()
        # m=MultiplayerMatch.objects.all().last()
        