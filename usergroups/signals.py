from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import UserGroup
from vacancies.models import Vacancy, Invitation, Application
from notify.utils import notify
from chat.models import ChatRoom
from django.utils.translation import gettext_lazy as _
from notify.utils import notify


@receiver(m2m_changed, sender=UserGroup.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    rooms = [ChatRoom.get_for_target(instance)]
    for vacancy in Vacancy.objects.filter(target_ct=UserGroup.content_type(), target_id=instance.id):
        for application in vacancy.applications.all():
            rooms.append(ChatRoom.get_for_target(application))
    if action == 'post_add':
        notify(instance.members.all().exclude(id=member.id), instance, 'has_new_member', member)
        for room in rooms:
            room.members.add(member)

    elif action == 'post_remove':
        notify(instance.members.all(), instance, 'has_lost_member', member)
        for room in rooms:
            room.members.remove(member)


@receiver(post_save, sender=UserGroup)
def group_created(instance, created, **kwargs):
    if instance.public and created:
        notify(instance.admin.friends(), instance.admin, 'created', instance)


@receiver(pre_save, sender=UserGroup)
def group_changed(instance, **kwargs):
    previous: UserGroup = UserGroup.objects.filter(id=instance.id).first()
    if previous:
        if previous.description != instance.description:
            notify(instance.members.all().exclude(id=instance.admin.id), instance, 'updated_description')

