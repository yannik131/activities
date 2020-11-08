from django.db.models.signals import post_save, m2m_changed, post_delete, pre_save
from django.dispatch import receiver
from .models import Appointment
from account.models import User
from actions.utils import create_action
from django.utils.translation import gettext_lazy as _


@receiver(m2m_changed, sender=Appointment.participants.through)
def appointment_confirmed(instance: Appointment, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        create_action(instance.group, _(': Jemand hat für den {stamp} zugesagt:').format(stamp=instance.start_time_formatted()), user)
    elif action == 'post_remove':
        create_action(instance.group, _(': Jemand hat für den {stamp} seine Zusage zurückgezogen:').format(stamp=instance.start_time_formatted()), user)


@receiver(m2m_changed, sender=Appointment.cancellations.through)
def appointment_cancelled(instance: Appointment, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        create_action(instance.group, _(': Jemand hat für den {stamp} abgesagt:').format(stamp=instance.start_time_formatted()), user)
    elif action == 'post_remove':
        create_action(instance.group, _(': Jemand hat für den {stamp} seine Absage zurückgezogen:').format(stamp=instance.start_time_formatted()), user)


@receiver(post_save, sender=Appointment)
def appointment_created(instance: Appointment, created, **kwargs):
    if created:
        create_action(instance.group, _('hat eine neue Terminabstimmung für den {stamp}').format(stamp=instance.start_time_formatted()))


@receiver(pre_save, sender=Appointment)
def appointment_saved(instance: Appointment, **kwargs):
    previous = Appointment.objects.filter(id=instance.id).first()
    if previous:
        if previous.start_time != instance.start_time:
            create_action(instance.group, _(': Der Termin am {stamp1} wurde auf den {stamp2} verlegt.').format(stamp1=previous.start_time_formatted(), stamp2=instance.start_time_formatted()))


@receiver(post_delete, sender=Appointment)
def appointment_deleted(instance: Appointment, **kwargs):
    create_action(instance.group, _(': Der Termin für den {stamp} wurde gelöscht.').format(stamp=instance.start_time_formatted()))