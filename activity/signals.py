from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Activity, Category
from notify.utils import notify
from account.models import User


@receiver(m2m_changed, sender=Activity.members.through)
def activity_members_changed(instance, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        notify(user.friends(), user, 'entered', instance)
    elif action == 'post_remove':
        notify(user.friends(), user, 'left', instance)
