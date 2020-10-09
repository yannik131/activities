from django.db import models
from account.models import User, Location
from activity.models import Activity
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class Opponent(models.Model):
    # 0 (loss), 0.5 (draw), 1.0 (win), 18 (skat: diamonds with 1), etc.
    points = models.FloatField(default=0.0)
    # black/white in chess, dealer/blinds in poker, etc.
    position = models.CharField(max_length=50, null=True, blank=True)
    instance_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='opponent_target_ct')
    instance_id = models.PositiveIntegerField(db_index=True)
    instance = GenericForeignKey('instance_ct', 'instance_id')  # This is either a User or a UserGroup
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(db_index=True)
    target = GenericForeignKey('target_ct', 'target_id') # This is either a Game, a Match or a Tournament


class Game(models.Model):
    match = models.ForeignKey('Match', on_delete=models.CASCADE, related_name='games')
    start_time = models.DateTimeField(blank=True, null=True)


class Match(models.Model):
    admin = models.ForeignKey(User, related_name='owned_matches', on_delete=models.CASCADE)
    is_team_match = models.BooleanField(default=False)
    start_time = models.DateTimeField()
    location = models.CharField(max_length=30)
    format = models.CharField(max_length=250)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='teams')
    tournament = models.ForeignKey('Tournament', on_delete=models.CASCADE, related_name='matches', null=True, blank=True)

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='competitions', model='match')


class Tournament(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='tournaments')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, related_name='tournaments', null=True)

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='competitions', model='tournament')
