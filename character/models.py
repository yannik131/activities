from django.db import models
from django.contrib.postgres.fields.hstore import HStoreField
from django.utils.translation import gettext_lazy as _
from activity.models import Activity
from django.urls import reverse
import json

BIG_FIVE = {
    'n': ['anx', 'ang', 'dep', 'con', 'imm', 'vul'],
    'e': ['fri', 'gre', 'ass', 'act', 'exc', 'che'],
    'o': ['ima', 'art', 'emo', 'adv', 'int', 'lib'],
    'a': ['tru', 'mor', 'alt', 'coo', 'mod', 'sym'],
    'c': ['eff', 'ord', 'dut', 'ach', 'dis', 'cau']
}

class Character(models.Model):
    traits = HStoreField(default=dict, blank=True)
    current_question = models.PositiveSmallIntegerField(default=0)
    suggestions = models.ManyToManyField(Activity, related_name='suggested_to')
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.init_traits()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('character:overview', args=[])
        
    def init_traits(self):
        for big in BIG_FIVE:
            for trait in BIG_FIVE[big]:
                self.traits[trait] = 0
                
    @property
    def traits_json(self):
        return json.dumps(self.traits)
