from django.db import models
from django.contrib.postgres.fields.hstore import HStoreField
from django.utils.translation import gettext_lazy as _
from activity.models import Activity
from django.urls import reverse
import json
from .utils import *
from shared.shared import log
from django.utils import timezone
from django.db.models import F


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
        
    @staticmethod
    def completed_quiz_count():
        return Character.objects.filter(current_question=F('question_limit')).count()
                
    @property
    def traits_json(self):
        return json.dumps(self.traits)
        
    @property
    def presentable(self):
        return self.current_question == self.question_limit
    
    def get_or_create_suggestions(self):
        if not self.last_calculation or self.last_calculation < Global.get().last_update:
            self.calculate_suggestions()
        return self.activity_suggestions
        
    def calculate_suggestions(self):
        self.activity_suggestions.all().delete()
        MAX_TRAIT_VALUE = 5*self.question_limit/30
        MIN_TRAIT_VALUE = 1*self.question_limit/30
        user_traits = to_numbers(self.traits)
        scores = []
        normalized = to_numbers(Global.get().normalized_traits)
        for activity in Activity.objects.all():
            if len(activity.trait_weights) == 0:
                continue
            score = 0
            max_score = 0
            for trait in activity.trait_weights:
                weight = json.loads(activity.trait_weights[trait])
                percent = round((user_traits[trait]-MIN_TRAIT_VALUE)/(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE)*100)
                score += weight[1]*calc_score(percent, normalized[trait], weight[0])
                max_score += weight[1]*100
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
        
class Global(models.Model):
    last_update = models.DateTimeField(default=timezone.now)
    normalized_traits = HStoreField(default=dict)
    UPDATE_COUNT = 1
    
    @staticmethod
    def get():
        return Global.objects.get_or_create()[0]
    
    @staticmethod
    def normalize_traits():
        if Character.completed_quiz_count() % Global.UPDATE_COUNT != 0:
            return
        single = Global.get()
        characters = Character.objects.filter(current_question=F('question_limit'))
        protection_count = 10
        n = characters.count()+protection_count
        summed_traits = create_trait_dict(default=50*protection_count)
        for traits, limit in characters.values_list('traits', 'question_limit'):
            MAX_TRAIT_VALUE = 5*limit/30
            MIN_TRAIT_VALUE = 1*limit/30
            for trait in summed_traits.keys():
                summed_traits[trait] += (int(traits[trait])-MIN_TRAIT_VALUE)/(MAX_TRAIT_VALUE-MIN_TRAIT_VALUE)*100
        for trait in summed_traits:
            summed_traits[trait] = round(summed_traits[trait]/n)
        single.normalized_traits = summed_traits
        single.last_update = timezone.now()
        single.save()
