from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class ActivityPage(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=150, blank=True)
    image = models.ImageField(upload_to='images/%Y/%m/%d/', blank=True, null=True)

    class Meta:
        ordering = ('name',)
        abstract = True


class Activity(ActivityPage):
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='activities', blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, related_name='activities', null=True, blank=True)
    TYPE_CHOICES = (
        ('competitive', 'kompetitiv'),
        ('creative', 'kreativ'),
        ('consumption', 'konsumorientiert')
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, null=True)

    def __str__(self):
        return self.name

    def verbose(self):
        return 'Aktivität: ' + self.name

    class Meta:
        verbose_name = 'Aktivität'
        verbose_name_plural = 'Aktivitäten'

    def get_absolute_url(self):
        return reverse('activity:detail', args=[self.name])

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='activity')


class Category(ActivityPage):
    def __str__(self):
        return self.name

    def verbose(self):
        return 'Kategorie: ' + self.name

    class Meta:
        verbose_name = 'Kategorie'
        verbose_name_plural = 'Kategorien'

    def get_absolute_url(self):
        return reverse('activity:category_detail', args=[self.id])

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='activity', model='category')
