from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Activity, Category
from actions.utils import create_action
from account.models import User
from django.utils.translation import gettext_lazy as _


@receiver(post_save, sender=Activity)
def activity_saved(instance, created, **kwargs):
    if created:
        create_action(instance, _('wurde erstellt.'))


@receiver(m2m_changed, sender=Activity.members.through)
def activity_members_changed(instance, action, pk_set, **kwargs):
    id = next(iter(pk_set))
    user = User.objects.get(id=id)
    if action == 'post_add':
        create_action(user, _('ist einer Aktivität beigetreten:'), instance)
    elif action == 'post_remove':
        create_action(user, _('hat eine Aktivität verlassen:'), instance)


@receiver(post_save, sender=Category)
def category_saved(instance, created, **kwargs):
    if created:
        create_action(instance, _('wurde erstellt.'))
