from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import ChatRoom
from .utils import broadcast

@receiver(m2m_changed, sender=ChatRoom.members.through)
def multiplayer_match_changed(instance, pk_set, model, action, **kwargs):
    if not pk_set:
        return
    if hasattr(instance.target, "members"):
        members = instance.target.members.all()
    else:
        return
    id = next(iter(pk_set))
    user = model.objects.get(id=id)
    if action == "post_add":
        broadcast(members, {
            'type': 'chat_message',
            'action': 'join',
            "username": user.username,
            'id': instance.id,
            'user_id': user.id,
            'url': user.image.url if user.image else ""
        })
    elif action == "post_remove":
        broadcast(members, {
            'type': 'chat_message',
            'action': 'leave',
            "username": user.username,
            'id': instance.id
        })