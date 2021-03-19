from django.db.models.signals import post_save, m2m_changed, post_delete, pre_save
from django.dispatch import receiver
from .models import Appointment
from account.models import User
from notify.utils import notify
from django.utils.translation import gettext_lazy as _


@receiver(m2m_changed, sender=Appointment.participants.through)
def appointment_confirmed(instance: Appointment, action, pk_set, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        notify(instance.group.members.all().exclude(id=user.id), user, 'confirmed', instance)
    elif action == 'post_remove':
        notify(instance.group.members.all().exclude(id=user.id), user, 'declined', instance)


@receiver(m2m_changed, sender=Appointment.cancellations.through)
def appointment_cancelled(instance: Appointment, action, pk_set, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        notify(instance.group.members.all().exclude(id=user.id), user, 'declined', instance)


@receiver(post_save, sender=Appointment)
def appointment_created(instance: Appointment, created, **kwargs):
    if created:
        notify(instance.group.members.all().exclude(id=instance.group.admin.id), instance.group, 'has_new_appointment', instance)


@receiver(pre_save, sender=Appointment)
def appointment_saved(instance: Appointment, **kwargs):
    if instance.pk is not None:
        previous = Appointment.objects.get(id=instance.id)
        if previous.start_time != instance.start_time:
            notify(instance.group.members.all(), instance.group.admin, 'has_moved_appointment', instance)
