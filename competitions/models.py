from django.db import models
from account.models import User, Location
from usergroups.models import UserGroup
from activity.models import Activity
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from vacancies.models import Vacancy
from shared import shared
from django.contrib.postgres.fields.hstore import HStoreField
import json
from django.utils.translation import gettext_lazy as _


class Game(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='games')
    start_time = models.DateTimeField(blank=True, null=True)


class Match(models.Model):
    admin = models.ForeignKey(User, related_name='owned_matches', on_delete=models.CASCADE)
    is_team_match = models.BooleanField(default=False)  # If this match is part of a tournament within a team based activity, this is true. User created team matches have to be created separately for this to be enabled
    start_time = models.DateTimeField()
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='matches')
    address = models.CharField(max_length=30)
    format = models.CharField(max_length=250)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='teams')
    round = models.ForeignKey('Round', on_delete=models.CASCADE, related_name='matches', null=True, blank=True)
    # TODO: Depending on activity this should have a more meaningful default value in the form
    public = models.BooleanField(default=True)
    points = HStoreField(default=dict)
    members = models.ManyToManyField(User, related_name='matches')
    groups = models.ManyToManyField(UserGroup, related_name='matches')

    def verbose(self):
        return str(self.activity) + "-" + self.__str__()

    def chat_allowed_for(self, user):
        return user in self.members.all()

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='competitions', model='match')

    def get_absolute_url(self):
        return reverse('competitions:match_detail', args=[self.id])

    def __str__(self):
        return _("Match am {start}").format(start=self.start_time)

    @property
    def vacancies(self):
        return Vacancy.objects.filter(target_ct=Match.content_type(), target_id=self.id)


class Tournament(models.Model):
    title = models.CharField(max_length=100)
    admin = models.ForeignKey(User, related_name='owned_tournaments', on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='tournaments')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='tournaments', null=True, blank=True)
    address = models.CharField(max_length=50, null=True, blank=True)
    members = models.ManyToManyField(User, related_name='tournaments')
    groups = models.ManyToManyField(UserGroup, related_name='tournaments')
    starting_time = models.DateTimeField()
    application_deadline = models.DateTimeField()
    max_members = models.PositiveSmallIntegerField(null=True, blank=True)
    fixed_number_of_rounds = models.PositiveSmallIntegerField(null=True, blank=True)
    format = models.TextField()
    points = HStoreField(default=dict)
    tie_breaks = HStoreField(default=dict)
    over = models.BooleanField(default=False)

    action_strings = {
        'started_new_round': _('hat eine neue Runde')
    }

    class Meta:
        unique_together = ('title', 'location')

    def get_absolute_url(self):
        return reverse('competitions:tournament_detail', args=[self.id])

    def __str__(self):
        return _("{act}-Turnier am {stamp}").format(act=self.activity, stamp=self.starting_time.strftime(shared.GERMAN_DATE_FMT))

    def verbose(self):
        return self.__str__()

    def chat_allowed_for(self, user):
        return self in user.tournaments.all() or user == self.admin

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='competitions', model='tournament')

    @property
    def vacancies(self):
        return Vacancy.objects.filter(target_ct=Tournament.content_type(), target_id=self.id)


class Round(models.Model):
    starting_time = models.DateTimeField(null=True)
    number = models.PositiveSmallIntegerField()
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='rounds')
    points = HStoreField(default=dict)
    matchups = models.JSONField(null=True)
    over = models.BooleanField(default=False)
    leftover = models.PositiveIntegerField(null=True)

    class Meta:
        ordering = ['number']

    def leftover_instance(self):
        if self.leftover:
            return User.objects.get(id=self.leftover)
        return None

    def matches_have_results(self):
        matchups = json.loads(self.matchups)
        for matchup in matchups:
            for user_id in matchup:
                if float(self.points[user_id]) != 0:
                    return True
        return False

    def matchup_players(self):
        matchups = json.loads(self.matchups)
        return [tuple(User.objects.get(id=int(k)) for k in matchup) for matchup in matchups]

    def get_absolute_url(self):
        return reverse('competitions:game_plan', args=[self.tournament.id, self.number])

    def __str__(self):
        return _('Runde ') + str(self.number)
