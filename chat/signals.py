from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import ChatRoom
from .utils import broadcast
from shared.shared import log

@receiver(m2m_changed, sender=ChatRoom.members.through)
def chat_members_changed(instance, pk_set, model, action, **kwargs):
    if not pk_set:
        return
    members = instance.members.all()
    id = next(iter(pk_set))
    user = model.objects.get(id=id)
    if action == "post_add":
        broadcast(members, {
            'type': 'chat_message',
            'action': 'join',
            "username": user.username,
            'sex': user.sex,
            'room_id': instance.id,
            'user_id': user.id,
            'url': user.image.url if user.image else "",
            'target': str(instance.get_target(user))
        })
    elif action == "pre_remove":
        broadcast(members, {
            'type': 'chat_message',
            'action': 'leave',
            "username": user.username,
            'user_id': user.id,
            'room_id': instance.id
        })
        if user.audio_room_id == instance.id:
            user.audio_room_id = None
            user.save()
        