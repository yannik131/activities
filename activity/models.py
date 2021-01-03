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
    image = models.ImageField(upload_to='images/activities/', blank=True, null=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='activities', blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, related_name='activities', null=True, blank=True)
    TYPE_CHOICES = (
        ('competitive', _('kompetitiv')),
        ('creative', _('kreativ')),
        ('consumption', _('konsumorientiert'))
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)
    online = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'activities'

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
    image = models.ImageField(upload_to='images/categories/', blank=True, null=True)

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
