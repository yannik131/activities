from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save, pre_save, pre_delete
from .models import User, Friendship, FriendRequest, Location
from notify.utils import notify
from chat.models import ChatRoom
from .utils import geocode
import time
from django.contrib.staticfiles.storage import staticfiles_storage
from shared.shared import log


@receiver(post_save, sender=FriendRequest)
def friend_request_saved(instance, created, **kwargs):
    if created:
        notify(instance.requested_user, instance.requesting_user, 'sent_friend_request', instance)


@receiver(post_save, sender=Friendship)
def friendship_saved(instance: Friendship, created, **kwargs):
    if created:
        notify(instance.from_user, instance.to_user, 'accepted_friend_request', url=instance.to_user.get_absolute_url())
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.from_user)
        room.members.add(instance.to_user)


@receiver(pre_delete, sender=Friendship)
def friendship_destroyed(instance: Friendship, **kwargs):
    ChatRoom.get_for_target(instance).delete()
    
@receiver(post_save, sender=Location)
def location_created(instance: Location, created, **kwargs):
    if instance.parent:
        return
    parent_components = instance.parent_components()
    if parent_components:
        components = dict(
            country=parent_components.get('country'),
            state=parent_components.get('state'),
            county=parent_components.get('county'),
            city=parent_components.get('city')
        )
        try:
            parent = Location.objects.get(**components)
        except Location.DoesNotExist:
            loc = geocode(parent_components)
            parent = Location.objects.create(**components, longitude=loc.longitude, latitude=loc.latitude)
        instance.parent = parent
        instance.save()
        