from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from .models import MultiplayerMatch


@receiver(m2m_changed, sender=MultiplayerMatch.members.through)
def multiplayer_match_changed(instance, pk_set, model, action, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    if action == "post_add":
        instance.broadcast_data(
            {
                'action': 'members_changed',
                "match_id": str(instance.id),
                "info": "joined",
                "position": instance.get_position_of(member),
                "username": member.username
            }, 
            direct=True
        )
        if instance.member_limit == instance.members.all().count():
            instance.broadcast_data(
                {
                    'action': 'members_changed',
                    "match_id": str(instance.id),
                    "info": "start"
                }, 
                direct=True
            )
            instance.start()
    elif action == "pre_remove":
        instance.broadcast_data(
            {
                'action': 'members_changed',
                "match_id": str(instance.id),
                "info": "left",
                "position": instance.get_position_of(member),
                "username": member.username
            },
            direct=True
        )
        
        
