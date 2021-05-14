from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from datetime import timedelta
from django.urls import reverse


class Notification(models.Model):
    LIFESPAN = timedelta(days=30)
    MAXIMUM = 10
    recipient = models.ForeignKey('account.User', on_delete=models.CASCADE, related_name='notifications')

    actor_ct = models.ForeignKey(ContentType, related_name='notify_actor', on_delete=models.CASCADE)
    actor_id = models.PositiveIntegerField()
    actor = GenericForeignKey('actor_ct', 'actor_id')

    action = models.CharField(max_length=50)

    action_object_ct = models.ForeignKey(ContentType, related_name='notify_action_object', blank=True, null=True, on_delete=models.CASCADE)
    action_object_id = models.PositiveIntegerField(blank=True, null=True)
    action_object = GenericForeignKey('action_object_ct', 'action_object_id')

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def get_absolute_url(self):
        if self.action == 'invited':
            return reverse('vacancies:application_list')
        if not self.action_object:
            return self.actor.get_absolute_url()
        return self.action_object.get_absolute_url()
        
    @property
    def should_be_deleted(self):
        return self.action_object_id and not self.action_object or self.actor is None or timezone.now()-self.timestamp > Notification.LIFESPAN

    def __str__(self):
        model = self.actor_ct.model_class()
        repr = f"{self.actor.verbose()} {model.action_strings[self.action]}"
        if self.action_object:
            return repr + f": {self.action_object.verbose()}"
        return repr
