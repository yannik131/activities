from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from .models import Post, Comment
from notify.utils import notify
from shared.shared import xor_get
import os
from django.utils.translation import gettext_lazy as _
from account.models import User


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


@receiver(m2m_changed, sender=Post.liked_by.through)
def post_liked(instance, action, pk_set, **kwargs):
    if not pk_set:
        return
    if action == 'post_add':
        id = next(iter(pk_set))
        user = User.objects.get(id=id)
        notify(instance.author, user, 'likes', instance)
        

@receiver(m2m_changed, sender=Post.disliked_by.through)
def post_disliked(instance, action, pk_set, **kwargs):
    if not pk_set:
        return
    if action == 'post_add':
        id = next(iter(pk_set))
        user = User.objects.get(id=id)
        notify(instance.author, user, 'dislikes', instance)