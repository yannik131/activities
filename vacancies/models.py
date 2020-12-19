from django.db import models
from account.models import User, FriendRequest
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _


class Invitation(models.Model):
    target_id = models.PositiveIntegerField()
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='invitation_target_ct')
    target = GenericForeignKey('target_ct', 'target_id')
    sender_id = models.PositiveIntegerField()
    sender_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    sender = GenericForeignKey('sender_ct', 'sender_id')
    message = models.CharField(max_length=50, null=True, blank=True)


class Vacancy(models.Model):
    # For USERS only, if you want a group, invite it!
    sex = models.CharField(max_length=1, choices=User.SEX_CHOICES, null=True, blank=True)
    min_age = models.PositiveSmallIntegerField(null=True, blank=True)
    max_age = models.PositiveSmallIntegerField(null=True, blank=True)
    description = models.CharField(max_length=50, null=True, blank=True)
    target_id = models.PositiveIntegerField()
    target_ct = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target = GenericForeignKey('target_ct', 'target_id')  # The object that has the vacancies: Match, UserGroup, ...
    COMPONENT_CHOICES = (
        ('country', _('Land')),
        ('state', _('Bundesland')),
        ('county', _('Landkreis')),
        ('city', _('Stadt'))
    )
    accepted = models.BooleanField(default=False)
    persistent = models.BooleanField(default=False)  # If True, the vacancy won't be deleted if an application is accepted
    location_component = models.CharField(max_length=40, choices=COMPONENT_CHOICES, default='city')
    location_component_value = models.CharField(max_length=40)

    def __str__(self):
        msg = self.description
        if self.min_age and not self.max_age:
            msg += _(' über {age}').format(age=self.min_age)
        elif self.max_age and not self.min_age:
            msg += _(' unter {age}').format(age=self.max_age)
        elif self.min_age and self.max_age:
            msg += _(' zwischen {age1} und {age2}').format(age1=self.min_age, age2=self.max_age)
        if self.sex:
            msg += _(', {sex}').format(sex=self.get_sex_display())
        else:
            msg += str(_(' (m/w)'))
        return msg

    def verbose(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('vacancies:review_vacancy', args=[self.id])


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='applications')
    message = models.CharField(max_length=250)
    status = models.CharField(max_length=15, choices=FriendRequest.STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ('status',)

    def chat_allowed_for(self, user):
        return user in [self.user, self.vacancy.target.admin] + list(self.vacancy.target.members.all())

    def __str__(self):
        return _('Bewerbung von {name}').format(name=self.user.username)

    def verbose(self):
        return _('{app} bei {target}').format(app=self.__str__(), target=self.vacancy.target)
