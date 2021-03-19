from django.db import models
from django.contrib.postgres.fields.hstore import HStoreField
from django.utils.translation import gettext_lazy as _
from activity.models import Activity, ActivityChange
from django.urls import reverse
import json
from .utils import *
from shared.shared import log, long_ago
from django.utils import timezone


class Suggestion(models.Model):
    character = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='activity_suggestions')
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE)
    score = models.PositiveSmallIntegerField()
    
    class Meta:
        ordering = ['character', '-score', 'activity']
    

class Character(models.Model):
    traits = HStoreField(default=dict, blank=True)
    current_question = models.PositiveSmallIntegerField(default=0)
    question_limit = models.PositiveSmallIntegerField(null=True)
    suggested_activities = models.ManyToManyField(Activity, related_name='suggested_to', through=Suggestion)
    last_calculation = models.DateTimeField(null=True)
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.traits = create_trait_dict()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('character:overview', args=[])
                
    @property
    def traits_json(self):
        return json.dumps(self.traits)
        
    @property
    def presentable(self):
        return self.current_question == self.question_limit
        
    def get_or_create_suggestions(self):
        if not self.last_calculation or self.last_calculation < ActivityChange.objects.first().last_update:
            self.calculate_suggestions()
        return self.activity_suggestions
        
    def calculate_suggestions(self):
        self.activity_suggestions.all().delete()
        MAX_TRAIT_VALUE = 5*self.question_limit/30
        MIN_TRAIT_VALUE = 1*self.question_limit/30
        user_traits = to_numbers(self.traits)
        scores = []
        for activity in Activity.objects.all():
            score = 0
            max_score = 0
            for trait in activity.trait_weights:
                weight = json.loads(activity.trait_weights[trait])
                if weight[0]:
                    score += weight[1]*(user_traits[trait]-MIN_TRAIT_VALUE)
                else:
                    score += weight[1]*(MAX_TRAIT_VALUE-user_traits[trait])
                max_score += weight[1]*(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE)
                
            if max_score > 0:
                scores.append((activity, round(score/max_score*100)))
        scores = sorted(scores, key=lambda t: t[1])
        for score in scores:
            Suggestion.objects.create(character=self, activity=score[0], score=score[1])
        self.last_calculation = timezone.now()
        self.save()
        
    def reset(self):
        self.current_question = 0
        self.question_limit = None
        self.traits = create_trait_dict()
        self.activity_suggestions.all().delete()
        self.last_calculation = None
        self.save()
