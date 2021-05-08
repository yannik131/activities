from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save, pre_save, pre_delete
from .models import User, Friendship, FriendRequest, Location
from notify.utils import notify
from chat.models import ChatRoom
from geopy import Nominatim
import time


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
    components = instance.parent_components()
    if components:
        geolocator = Nominatim(user_agent='activities')
        loc = geolocator.geocode(components)
        time.sleep(0.5)
        print(instance)
        parent, created = Location.objects.get_or_create(
            country=components.get('country'),
            state=components.get('state'),
            county=components.get('county'),
            city=components.get('city'),
            latitude=round(loc.latitude, 6),
            longitude=round(loc.longitude, 6)
    )
        instance.parent = parent
        instance.save()
        