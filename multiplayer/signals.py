from django.db.models.signals import m2m_changed, pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import MultiplayerMatch
from shared.shared import log
from chat.models import ChatRoom
import json

@receiver(m2m_changed, sender=MultiplayerMatch.members.through)
def multiplayer_match_changed(instance, pk_set, model, action, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == "post_add":
        room.members.add(member)
    elif action == "post_remove":
        room.members.remove(member)
        
        
@receiver(pre_delete, sender=MultiplayerMatch)
def match_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    instance.abort(redirect_to_lobby=True)
        
