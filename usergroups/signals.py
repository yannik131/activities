from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver
from .models import UserGroup
from vacancies.models import Vacancy, Invitation, Application
from actions.utils import create_action
from chat.models import ChatRoom


@receiver(m2m_changed, sender=UserGroup.members.through)
def members_changed(instance, action, model, pk_set, **kwargs):
    id = next(iter(pk_set))
    member = model.objects.get(id=id)
    rooms = [ChatRoom.get_for_target(instance)]
    for vacancy in Vacancy.objects.filter(target_ct=UserGroup.content_type(), target_id=instance.id):
        for application in vacancy.applications.all():
            rooms.append(ChatRoom.get_for_target(application))
    if action == 'post_add':
        create_action(instance, 'hat ein neues Mitglied:', member)
        for room in rooms:
            room.members.add(member)

    elif action == 'post_remove':
        create_action(member, 'ist kein Mitglied mehr von:', instance)
        for room in rooms:
            room.members.remove(member)


@receiver(post_save, sender=UserGroup)
def group_created(instance, created, **kwargs):
    if instance.public and created:
        create_action(instance.admin, 'hat eine Gruppe erstellt:', instance)


@receiver(pre_save, sender=UserGroup)
def group_changed(instance, **kwargs):
    previous: UserGroup = UserGroup.objects.filter(id=instance.id).first()
    if previous:
        if previous.description != instance.description:
            create_action(instance, 'hat seine Beschreibung aktualisiert')


@receiver(post_delete, sender=UserGroup)
def group_deleted(instance, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    if instance.public:
        create_action(instance.admin, f'hat eine Gruppe gelöscht: {instance.name}', instance)


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
    create_action(instance.sender, 'hat eine Einladung gelöscht mit folgendem Empfänger:', instance.target)


@receiver(post_save, sender=Application)
def application_created(instance: Application, created, **kwargs):
    if created:
        create_action(instance.user, f'hat sich auf eine Leerstelle beworben: "{instance.vacancy}", von:', instance.vacancy.group)
        room = ChatRoom.get_for_target(instance)
        room.members.add(instance.user)
        for member in instance.vacancy.group.members.all():
            room.members.add(member)


@receiver(pre_save, sender=Application)
def application_saved(instance: Application, **kwargs):
    previous = Application.objects.filter(id=instance.id).first()
    if previous:
        if previous.status != instance.status:
            create_action(instance.vacancy.group, f'hat den Status der Bewerbung auf die Leerstelle {instance.vacancy} auf {instance.get_status_display} geändert. Bewerber:', instance.user)
            ChatRoom.get_for_target(instance).delete()


@receiver(post_delete, sender=Application)
def application_deleted(instance: Application, **kwargs):
    room = ChatRoom.get_for_target(instance)
    room.delete()
    create_action(instance.vacancy.group, f'Die Bewerbung auf die Leerstelle "{instance.vacancy}" wurde gelöscht. Bewerber:', instance.user)
