from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save, post_delete, pre_save
from .models import User, Friendship, FriendRequest
from notify.utils import notify
from chat.models import ChatRoom
from django.utils.translation import gettext_lazy as _


@receiver(post_save, sender=FriendRequest)
def friend_request_saved(instance, created, **kwargs):
    if created:
        notify(instance.requested_user, instance.requesting_user, 'sent_friend_request', instance)


@receiver(post_save, sender=Friendship)
def friendship_saved(instance: Friendship, created, **kwargs):
    if created:
        notify(instance.from_user.friends(), instance.from_user, 'has_new_friend', instance.to_user)
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.from_user)
        room.members.add(instance.to_user)


@receiver(post_delete, sender=Friendship)
def friendship_destroyed(instance: Friendship, **kwargs):
    notify(instance.from_user, instance.to_user, 'has_lost_friend')
    notify(instance.to_user, instance.from_user, 'terminated_friendship')
    ChatRoom.get_for_target(instance).delete()