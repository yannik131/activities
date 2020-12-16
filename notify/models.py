from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from model_utils import Choices
from account.models import User
from django.utils import timezone


class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE)

    actor_ct = models.ForeignKey(ContentType, related_name='notify_actor', on_delete=models.CASCADE)
    actor_id = models.PositiveIntegerField()
    actor = GenericForeignKey('actor_ct', 'actor_id')

    ACTION_CHOICES = Choices('created', 'deleted', 'accepted', 'rejected')
    action = models.CharField(choices=ACTION_CHOICES, max_length=50)

    action_object_ct = models.ForeignKey(ContentType, related_name='notify_action_object', blank=True, null=True, on_delete=models.CASCADE)
    action_object_id = models.PositiveIntegerField(blank=True, null=True)
    action_object = GenericForeignKey('action_object_ct', 'action_object_id')

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        model = self.actor_ct.model_class()
        repr = f"{self.actor.verbose()} {model.action_strings[self.action]}"
        if self.action_object:
            return repr + f" {self.action_object.verbose()}"
        return repr
