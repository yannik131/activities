from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from vacancies.models import Vacancy, Invitation, Application
from actions.utils import create_action
from chat.models import ChatRoom


@receiver(post_save, sender=Vacancy)
def vacancy_changed(instance, created, **kwargs):
    if created:
        create_action(instance.target, 'hat eine neue Leerstelle:', instance)
    else:
        create_action(instance.target, 'hat eine Leerstelle angepasst: ' + str(instance))


@receiver(post_save, sender=Invitation)
def vacancy_changed(instance, created, **kwargs):
    if created:
        create_action(instance.sender, 'hat jemanden eingeladen:', instance.target)
    else:
        create_action(instance.sender, 'hat eine Einladung verändert an:', instance.target)


@receiver(post_delete, sender=Vacancy)
def vacancy_deleted(instance, **kwargs):
    create_action(instance.target, 'hat folgende Leerstelle gelöscht: ' + str(instance))


@receiver(post_delete, sender=Invitation)
def invitation_deleted(instance, **kwargs):
    if instance.target in instance.sender.members.all():
        return
    create_action(instance.sender, 'hat eine Einladung gelöscht mit folgendem Empfänger:', instance.target)


@receiver(post_save, sender=Application)
def application_created(instance: Application, created, **kwargs):
    if created:
        create_action(instance.user, f'hat sich auf eine Leerstelle beworben: "{instance.vacancy}", von:', instance.vacancy.target)
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.user)
        for member in instance.vacancy.target.members.all():
            room.members.add(member)


@receiver(pre_save, sender=Application)
def application_saved(instance: Application, **kwargs):
    previous = Application.objects.filter(id=instance.id).first()
    if previous:
        if previous.status != instance.status:
            create_action(instance.vacancy.target, f'hat den Status der Bewerbung auf die Leerstelle {instance.vacancy} auf {instance.get_status_display} geändert. Bewerber:', instance.user)
            ChatRoom.get_for_target(instance).delete()


@receiver(post_delete, sender=Application)
def application_deleted(instance: Application, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    create_action(instance.vacancy.target, f'Die Bewerbung auf die Leerstelle "{instance.vacancy}" wurde gelöscht. Bewerber:', instance.user)
