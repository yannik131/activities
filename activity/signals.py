from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Activity, ActivityChange
from notify.utils import notify
from account.models import User
from shared.shared import log
from django.utils import timezone


@receiver(m2m_changed, sender=Activity.members.through)
def activity_members_changed(instance, action, pk_set, **kwargs):
    if not pk_set:
        return
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        notify(user.friends(), user, 'entered', instance)
    elif action == 'post_remove':
        notify(user.friends(), user, 'left', instance)
        

@receiver(pre_save, sender=Activity)
def activity_saved(instance, **kwargs):
    if instance.pk is not None:
        previous = Activity.objects.get(pk=instance.pk)
        if previous.trait_weights != instance.trait_weights:
            change = ActivityChange.objects.first()
            change.last_update = timezone.now()
            change.save()
