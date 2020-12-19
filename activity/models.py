from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from parler.models import TranslatableModel, TranslatedFields


class Activity(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=30, unique=True, db_index=True),
        description=models.CharField(max_length=150, blank=True)
    )
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='activities', blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, related_name='activities', null=True, blank=True)
    TYPE_CHOICES = (
        ('competitive', _('kompetitiv')),
        ('creative', _('kreativ')),
        ('consumption', _('konsumorientiert'))
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)

    def __str__(self):
        return self.name

    def verbose(self):
        return _('Aktivität: {name}').format(name=self.name)

    def get_absolute_url(self):
        return reverse('activity:detail', args=[self.name])

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='activity')


class Category(TranslatableModel):
    translations = TranslatedFields(
        name=models.CharField(max_length=30, unique=True, db_index=True),
        description=models.CharField(max_length=150, blank=True)
    )
    image = models.ImageField(upload_to='images/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return self.name

    def verbose(self):
        return _('Kategorie: {name}').format(name=self.name)

    def get_absolute_url(self):
        return reverse('activity:category_detail', args=[self.name])

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='category')
