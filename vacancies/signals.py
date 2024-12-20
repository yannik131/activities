from django.db.models.signals import m2m_changed, post_save, pre_save, pre_delete
from django.dispatch import receiver
from vacancies.models import Vacancy, Invitation, Application
from notify.utils import notify
from chat.models import ChatRoom
from account.models import User
from django.utils.translation import gettext_lazy as _
from shared.shared import log


@receiver(post_save, sender=Application)
def application_created(instance: Application, created, **kwargs):
    if created:
        notify(instance.vacancy.target.members.all(), instance.user, 'applied_for', instance.vacancy)
        if instance.vacancy.target.admin not in instance.vacancy.target.members.all():
            notify(instance.vacancy.target.admin, instance.user, 'applied_for', instance.vacancy)
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.user)
        for member in instance.vacancy.target.members.all():
            room.members.add(member)


@receiver(pre_save, sender=Application)
def application_saved(instance: Application, **kwargs):
    if instance.pk is not None:
        previous = Application.objects.get(id=instance.id)
        if previous.status != instance.status:
            ChatRoom.get_for_target(instance).delete()
            if instance.status == 'declined':
                notify(instance.user, instance.vacancy.target.admin, 'declined_application', instance, url=instance.vacancy.target.get_absolute_url())


@receiver(pre_delete, sender=Application)
def application_deleted(instance: Application, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()


@receiver(post_save, sender=Invitation)
def invitation_created(instance, created, **kwargs):
    notify(instance.target, instance.sender.admin, 'invited', instance.sender)
