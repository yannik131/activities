from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields
from character.utils import BIG_FIVE, create_trait_dict
from django.contrib.postgres.fields.hstore import HStoreField
import json
from django.utils import timezone
        

def activity_directory_path(instance, filename):
        return f"activities/{instance.name}.{filename.split('.')[-1]}"
    

class Activity(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=30,  db_index=True),
        description=models.CharField(max_length=150, blank=True)
    )
    image = models.ImageField(upload_to=activity_directory_path, blank=True, null=True)
    image_url = models.URLField(null=True, blank=True)
    image_source = models.URLField(null=True, blank=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='activities', blank=True)
    TYPE_CHOICES = (
        ('competitive', _('kompetitiv')),
        ('creative', _('kreativ')),
        ('consumption', _('konsumorientiert'))
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True, blank=True)
    online = models.BooleanField(default=False)
    trait_weights = HStoreField(default=dict, blank=True)
    
    class Meta:
        verbose_name_plural = 'activities'
        ordering = ['-pk', 'type']

    def __str__(self):
        return self.name

    def verbose(self):
        return _('Aktivität: {name}').format(name=self.name)

    def get_absolute_url(self):
        return reverse('activity:detail', args=[self.name])
        
    @property
    def channel_group_name(self):
        return f"activity-{self.id}"

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='activity')
        
    def lobby_url(self, request=None):
        if request:
            return request.build_absolute_uri(f'/multiplayer/lobby/{self.name}/')
        else:
            return f'/multiplayer/lobby/{self.name}/'
            
    def chat_allowed_for(self, user):
        return user.activities.filter(pk=self.pk).exists()
        
    @property
    def weights_json(self):
        return json.dumps(self.trait_weights)

def category_directory_path(instance, filename):
        return f"categories/{instance.name}.{filename.split('.')[-1]}"
        

class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=30, unique=True, db_index=True),
        description=models.CharField(max_length=150, blank=True)
    )
    image = models.ImageField(upload_to=category_directory_path, blank=True, null=True)
    image_url = models.URLField(null=True, blank=True)
    image_source = models.URLField(null=True, blank=True)
    activities = models.ManyToManyField(Activity, related_name='categories', blank=True)
    parent_category = models.ForeignKey('Category', related_name='sub_categories', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def verbose(self):
        return _('Kategorie: {name}').format(name=self.name)

    def get_absolute_url(self):
        return reverse('activity:category_detail', args=[self.name])

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='category')
