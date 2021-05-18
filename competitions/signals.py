from django.db.models.signals import m2m_changed, post_save, pre_save, pre_delete
from django.dispatch import receiver
from .models import Match, Tournament, Round
from notify.utils import notify
from chat.models import ChatRoom
from django.utils.translation import gettext_lazy as _
from vacancies.utils import clear_vacancies_for


@receiver(m2m_changed, sender=Match.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == 'post_add':
        notify(instance.members.all(), member, 'entered', instance)
        room.members.add(member)

    elif action == 'post_remove':
        notify(instance.members.all(), member, 'left', instance)
        room.members.remove(member)


@receiver(m2m_changed, sender=Tournament.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    room = ChatRoom.get_for_target(instance)
    if action == 'post_add':
        notify(instance.members.all(), member, 'entered', instance)
        instance.points[str(member.id)] = 0
        instance.tie_breaks[str(member.id)] = 0
        room.members.add(member)
    elif action == 'post_remove':
        notify(instance.members.all(), member, 'left', instance)
        del instance.points[str(member.id)]
        del instance.tie_breaks[str(member.id)]
        room.members.remove(member)

    instance.save()


@receiver(post_save, sender=Match)
def match_created(instance, created, **kwargs):
    if created:
        notify(instance.admin.friends(), instance.admin, 'created', instance)
        instance.members.add(instance.admin)


@receiver(pre_delete, sender=Match)
def match_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    clear_vacancies_for(instance)


@receiver(post_save, sender=Tournament)
def tournament_created(instance, created, **kwargs):
    if created:
        notify(instance.admin.friends(), instance.admin, 'created', instance)
    room = ChatRoom.get_for_target(instance)
    room.members.add(instance.admin)


@receiver(pre_delete, sender=Tournament)
def tournament_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    clear_vacancies_for(instance)


@receiver(post_save, sender=Round)
def round_created(instance, created, **kwargs):
    if created:
        notify(instance.tournament.members.all(), instance.tournament, 'started_new_round', instance)
