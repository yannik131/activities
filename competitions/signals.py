from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import Match
from actions.utils import create_action
from chat.models import ChatRoom


@receiver(m2m_changed, sender=Match.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == 'post_add':
        create_action(instance, 'hat ein neuen Mitspieler:', member)
        room.members.add(member)

    elif action == 'post_remove':
        create_action(member, 'ist kein Mitspieler mehr bei:', instance)
        room.members.remove(member)


@receiver(post_save, sender=Match)
def match_created(instance, created, **kwargs):
    if created:
        instance.members.add(instance.admin)


@receiver(post_delete, sender=Match)
def match_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    if instance.public:
        create_action(instance.admin, f'hat ein Match gelöscht: {instance}', instance)