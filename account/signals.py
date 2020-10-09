from django.dispatch import receiver
from django.db.models.signals import m2m_changed, post_save, post_delete
from .models import User, Friendship
from actions.utils import create_action
from chat.models import ChatRoom


@receiver(post_save, sender=Friendship)
def friendship_saved(instance: Friendship, created, **kwargs):
    if created:
        create_action(instance.from_user, 'ist jetzt befreundet mit', instance.to_user)
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.from_user)
        room.members.add(instance.to_user)


@receiver(post_delete, sender=Friendship)
def friendship_destroyed(instance: Friendship, **kwargs):
    create_action(instance.from_user, 'ist nicht mehr befreundet mit', instance.to_user)
    ChatRoom.get_for_target(instance).delete()