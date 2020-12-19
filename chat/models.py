from django.db import models
from account.models import User, Friendship
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from django.utils.timezone import now


class ChatCheck(models.Model):
    room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, related_name='last_checks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='last_chat_checks')
    date = models.DateTimeField(auto_now_add=True)

    def new_messages(self):
        return self.room.log_entries.filter(created__gt=self.date).exclude(author=self.user)

    def update(self):
        self.date = now()
        self.save()


class ChatRoom(models.Model):
    members = models.ManyToManyField(User, related_name='chat_rooms', through=ChatCheck)
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveIntegerField(db_index=True)
    target = GenericForeignKey('target_ct', 'target_id')

    class Meta:
        unique_together = ('target_ct', 'target_id')

    @staticmethod
    def get(app_label, model, id):
        ct = ContentType.objects.get(app_label=app_label, model=model)
        target = ct.get_object_for_this_type(pk=id)
        room, created = ChatRoom.objects.get_or_create(target_ct=ct, target_id=target.id)
        return room

    @staticmethod
    def get_for_target(target):
        ct = ContentType.objects.get_for_model(target)
        room, created = ChatRoom.objects.get_or_create(target_ct=ct, target_id=target.id)
        return room

    def is_allowed_here(self, user):
        return self.target.chat_allowed_for(user)

    def get_absolute_url(self):
        return reverse('chat:chat_room', args=[self.target_ct.app_label, self.target_ct.model, self.target_id])

    def title_for_friendship(self, user):
        if user == self.target.to_user:
            return str(self.target.from_user)
        return str(self.target.to_user)

    def title_for(self, user):
        if self.target_ct == Friendship.content_type():
            return self.title_for_friendship(user)
        return str(self.target.verbose())


class ChatLogEntry(models.Model):
    MAX_NUMBER_OF_LOG_ENTRIES = 10
    text = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    chat_room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='log_entries')
    created = models.DateTimeField()

    class Meta:
        ordering = ('created',)

    def __str__(self):
        return self.text

    def full_origin(self, user):
        if self.chat_room.target_ct == Friendship.content_type():
            return self.chat_room.title_for_friendship(user)
        return str(self.chat_room.target.verbose()) + ", " + self.author.username

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        messages = self.chat_room.log_entries.all()
        if messages.count() > ChatLogEntry.MAX_NUMBER_OF_LOG_ENTRIES:
            messages.first().delete()
