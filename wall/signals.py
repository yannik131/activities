from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Comment
from actions.utils import create_action
from shared.shared import xor_get
import os
from django.utils.translation import gettext_lazy as _


@receiver(post_save, sender=Post)
def post_created(instance: Post, created, **kwargs):
    if created:
        create_action(instance.author, _('hat etwas gepostet in:'), instance.target)


@receiver(post_delete, sender=Post)
def post_deleted(instance: Post, **kwargs):
    file = xor_get([instance.audio, instance.video, instance.image])
    if file and os.path.isfile(file.path):
        os.remove(file.path)
    # TODO: Delete the corresponding actions in every model deletion


@receiver(post_save, sender=Comment)
def comment_created(instance: Comment, created, **kwargs):
    if created:
        create_action(instance.author, _('hat etwas kommentiert:'), instance.post.target)
