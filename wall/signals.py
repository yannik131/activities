from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Post, Comment
from notify.utils import notify
from shared.shared import xor_get
import os
from django.utils.translation import gettext_lazy as _


@receiver(post_save, sender=Post)
def post_created(instance: Post, created, **kwargs):
    if created:
        notify(instance.author.friends(), instance.author, 'posted_in', instance.target)


@receiver(post_delete, sender=Post)
def post_deleted(instance: Post, **kwargs):
    file = xor_get([instance.audio, instance.video, instance.image])
    if file and os.path.isfile(file.path):
        os.remove(file.path)


@receiver(post_save, sender=Comment)
def comment_created(instance: Comment, created, **kwargs):
    if created:
        notify(instance.author.friends(), instance.author, 'commented_in', instance.post.target)
