from django.db.models.signals import post_save, m2m_changed, post_delete, pre_save
from django.dispatch import receiver
from .models import Appointment
from account.models import User
from actions.utils import create_action


@receiver(m2m_changed, sender=Appointment.participants.through)
def appointment_confirmed(instance: Appointment, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        create_action(instance.group, f': Jemand hat für den {instance.start_time_formatted()} zugesagt:', user)
    elif action == 'post_remove':
        create_action(instance.group, f': Jemand hat für den {instance.start_time_formatted()} seine Zusage zurückgezogen:', user)


@receiver(m2m_changed, sender=Appointment.cancellations.through)
def appointment_cancelled(instance: Appointment, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        create_action(instance.group, f': Jemand hat für den {instance.start_time_formatted()} abgesagt:', user)
    elif action == 'post_remove':
        create_action(instance.group, f': Jemand hat für den {instance.start_time_formatted()} seine Absage zurückgezogen:', user)


@receiver(post_save, sender=Appointment)
def appointment_created(instance: Appointment, created, **kwargs):
    if created:
        create_action(instance.group, f'hat eine neue Terminabstimmung für den {instance.start_time_formatted()}')


@receiver(pre_save, sender=Appointment)
def appointment_saved(instance: Appointment, **kwargs):
    previous = Appointment.objects.filter(id=instance.id).first()
    if previous:
        if previous.start_time != instance.start_time:
            create_action(instance.group, f': Der Termin am {previous.start_time_formatted()} wurde auf den {instance.start_time_formatted()} verlegt. ')


@receiver(post_delete, sender=Appointment)
def appointment_deleted(instance: Appointment, **kwargs):
    create_action(instance.group, f': Der Termin für den {instance.start_time_formatted()} wurde gelöscht.')