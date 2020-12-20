from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save, post_delete, pre_save
from .models import User, Friendship, FriendRequest
from notify.utils import notify
from chat.models import ChatRoom


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


@receiver(post_delete, sender=Friendship)
def friendship_destroyed(instance: Friendship, **kwargs):
    ChatRoom.get_for_target(instance).delete()