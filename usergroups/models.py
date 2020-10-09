from django.db import models
from account.models import User
from activity.models import Category
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType


class UserGroup(models.Model):
    admin = models.ForeignKey(User, related_name='owned_groups', on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=150, null=True, blank=True)
    members = models.ManyToManyField(User, related_name='user_groups', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='groups')
    public = models.BooleanField(default=True)

    class Meta:
        unique_together = ('name', 'category')

    def set_admin(self, admin):
        self.admin = admin
        if admin not in self.members.all():
            self.members.add(admin)

    def __str__(self):
        return self.name

    def verbose(self):
        return 'Gruppe: ' + self.name

    def save(self, *args, **kwargs):
        new = self.pk is None
        super().save()
        if new and self.admin not in self.members.all():
            self.members.add(self.admin)

    def get_absolute_url(self):
        return reverse('usergroups:group_detail', args=[self.id])

    def chat_allowed_for(self, user):
        return user in self.members.all()

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='usergroups', model='usergroup')
