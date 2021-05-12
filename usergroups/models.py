from django.db import models
from account.models import User
from activity.models import Category
from django.urls import reverse
from vacancies.models import Vacancy, Invitation
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from asgiref.sync import async_to_sync


class UserGroup(models.Model):
    image = models.ImageField(upload_to='groups/%Y/%m/%d/', blank=True, null=True)
    admin = models.ForeignKey(User, related_name='owned_groups', on_delete=models.PROTECT)
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=150, null=True, blank=True)
    members = models.ManyToManyField(User, related_name='user_groups', blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='groups')
    public = models.BooleanField(default=True)

    action_strings = {
        'has_new_appointment': _('hat einen neuen Termin'),
        'has_moved_appointment': _('hat einen Termin verschoben'),
        'has_new_member': _('hat ein neues Mitglied'),
        'has_lost_member': _('hat ein Mitglied verloren'),
        'updated_description': _('hat eine neue Beschreibung'),
        'accepted_application': _('hat Ihre Bewerbung angenommen'),
        'kicked_you_out': _("hat Sie rausgeschmissen")
    }

    class Meta:
        unique_together = ('name', 'category')
        
    @property
    def get_image(self):
        if self.image:
            return self.image
        return 'static/icons/group.png'

    def __str__(self):
        return self.name

    def verbose(self):
        return _('Gruppe: {name}').format(name=self.name)

    def save(self, *args, **kwargs):
        new = self.pk is None
        super().save()
        if new and self.admin not in self.members.all():
            self.members.add(self.admin)

    def get_absolute_url(self):
        return reverse('usergroups:group_detail', args=[self.id])

    def chat_allowed_for(self, user):
        return user in self.members.all()
        
    def broadcast_message(self, message):
        for member in self.members.all():
            if member.channel_name:
                async_to_sync(self.channel_layer.send)(
                    member.channel_name,
                    message
                )

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='usergroups', model='usergroup')

    @property
    def vacancies(self):
        return Vacancy.objects.filter(target_ct=UserGroup.content_type(), target_id=self.id)

    @property
    def invitations(self):
        return Invitation.objects.filter(sender_ct=UserGroup.content_type(), sender_id=self.id)
