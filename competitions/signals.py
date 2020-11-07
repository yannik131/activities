from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import Match, Tournament
from actions.utils import create_action
from chat.models import ChatRoom
from django.utils.translation import gettext_lazy as _


@receiver(m2m_changed, sender=Match.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == 'post_add':
        create_action(instance, _('hat ein neuen Mitspieler:'), member)
        room.members.add(member)

    elif action == 'post_remove':
        create_action(member, _('ist kein Mitspieler mehr bei:'), instance)
        room.members.remove(member)


@receiver(m2m_changed, sender=Tournament.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == 'post_add':
        instance.points[str(member.id)] = 0
        instance.tie_breaks[str(member.id)] = 0
        room.members.add(member)
    elif action == 'post_remove':
        del instance.points[str(member.id)]
        del instance.tie_breaks[str(member.id)]
        room.members.remove(member)

    instance.save()


@receiver(post_save, sender=Match)
def match_created(instance, created, **kwargs):
    if created:
        instance.members.add(instance.admin)


@receiver(post_delete, sender=Match)
def match_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    create_action(instance.admin, _('hat ein Match gelöscht: {instance}').format(instance=instance), instance)


@receiver(post_save, sender=Tournament)
def tournament_created(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.members.add(instance.admin)


@receiver(post_delete, sender=Tournament)
def tournament_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
