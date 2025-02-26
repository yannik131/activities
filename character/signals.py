from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Character


@receiver(post_save, sender=Character)
def character_saved(instance, created, **kwargs):
    pass