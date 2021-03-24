from django.db import models
from django.contrib.auth.models import AbstractUser
import geopy
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from itertools import chain
from django.utils.translation import gettext_lazy as _
from character.models import Character

class User(AbstractUser):
    profile_text = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.CASCADE, blank=True, related_name='population')
    latest_request_check = models.DateTimeField(default=timezone.now)
    birth_year = models.PositiveSmallIntegerField(null=True)
    SEX_CHOICES = (
        ('m', _('männlich')),
        ('w', _('weiblich'))
    )
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True)
    confirmed_appointments = models.ManyToManyField("scheduling.Appointment", related_name='participants')
    cancelled_appointments = models.ManyToManyField("scheduling.Appointment", related_name='cancellations')
    channel_name = models.CharField(max_length=100, null=True)
    character = models.OneToOneField(Character, on_delete=models.SET_NULL, null=True, related_name='user')
    action_strings = {
        'created': _('hat erstellt'),
        'has_new_friend': _('ist jetzt befreundet mit'),
        'has_lost_friend': _('ist nicht mehr befreundet mit'),
        'sent_friend_request': _('hat Ihnen eine Freundschaftsanfrage geschickt'),
        'entered': _('ist beigetreten'),
        'left': _('hat verlassen'),
        'confirmed': _('hat zugesagt'),
        'declined': _('hat abgesagt'),
        'applied_for': _('hat sich beworben'),
        'posted_in': _('hat etwas gepostet in'),
        'commented_in': _('hat etwas kommentiert'),
        'terminated_friendship': _('hat eure Freundschaft beendet'),
        'invited': _('hat Sie eingeladen'),
        'accepted_friend_request': _('hat Ihre Freundschaftsanfrage angenommen'),
        'declined_friend_request': _('hat Ihre Freundschaftsanfrage abgelehnt'),
        'declined_application': _('hat Ihre Bewerbung abgelehnt'),
        'likes': _('gefällt'),
        'dislikes': _('missfällt')
    }

    def friendships(self):
        return list(chain(self.from_friendships.all(), self.to_friendships.all()))

    def get_friendship_for(self, user):
        return next((friendship for friendship in self.friendships() if friendship.to_user == user or friendship.from_user == user), None)

    def friends(self):
        return [f.get_other_user(self) for f in self.friendships()]

    def get_latest_messages(self):
        chat_checks = self.last_chat_checks.all()
        log_entries = list()
        for check in chat_checks:
            messages = check.new_messages()
            if messages:
                log_entries.append(messages.last())
        log_entries = sorted(log_entries, key=lambda entry: entry.created)
        return log_entries
        
    def rooms_with_news(self):
        chat_checks = self.last_chat_checks.all()
        rooms = []
        for check in chat_checks:
            if check.new_messages():
                rooms.append(check.room.id)
        return rooms

    def get_absolute_url(self):
        return reverse('account:detail', args=[self.username])

    def __str__(self):
        return self.username

    def verbose(self):
        return self.__str__()

    def get_age(self):
        return timezone.now().year - self.birth_year

    def get_full_name(self):
        if self.first_name and self.last_name:
            return super().get_full_name()
        elif self.first_name and not self.last_name:
            return self.first_name
        return None

    def satisfies_requirements_of(self, vacancy):
        if not self.location.equal_to(vacancy.target.admin.location, vacancy.location_component):
            return False
        if vacancy.sex and self.sex != vacancy.sex:
            return False
        age = timezone.now().year - self.birth_year
        if vacancy.min_age and age < vacancy.min_age or \
                vacancy.max_age and age > vacancy.max_age:
            return False
        return True

    def chat_allowed_for(self, user):
        return user in self.friends.all()

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='account', model='user')

    def application_dict(self):
        return dict([(a.vacancy.id, a.status) for a in self.applications.all()])
        
    def init_traits(self):
        for trait in User.CHARACTER_TRAITS:
            self.character[trait] = 0
        self.save()
        
    @property
    def channel_group_name(self):
        return f"user-{self.id}"
        
    @property
    def get_notifications(self):
        notifications = []
        for notification in self.notifications.all():
            if notification.action_object_id and not notification.action_object:
                notification.delete()
            else:
                notifications.append(notification)
        return notifications


class Friendship(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='from_friendships')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='to_friendships')

    def __str__(self):
        return f'{self.from_user}-{self.to_user}'

    def verbose(self):
        return self.__str__()

    class Meta:
        unique_together = ('from_user', 'to_user')

    def chat_allowed_for(self, user):
        return user in [self.from_user, self.to_user]

    def get_absolute_url(self):
        return reverse('account:view_friendship', args=[self.id])
        
    def get_other_user(self, user):
        if user == self.from_user:
            return self.to_user
        return self.from_user

    @staticmethod
    def content_type():
        return ContentType.objects.get(app_label='account', model='friendship')


class FriendRequest(models.Model):
    requesting_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_friend_requests')
    requested_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_friend_requests')
    STATUS_CHOICES = (
        ('pending', _('Ausstehend')),
        ('accepted', _('Angenommen')),
        ('declined', _('Abgelehnt')),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    request_message = models.CharField(max_length=150)

    def set_status(self, status):
        if self.status != 'pending':
            return
        other_request = FriendRequest.objects.filter(
            requested_user=self.requesting_user,
            requesting_user=self.requested_user)
        other_request.update(status=status)
        self.status = status
        self.save()

    def __str__(self):
        return self.request_message

    def verbose(self):
        return self.__str__()

    def get_absolute_url(self):
        return reverse('account:friend_requests_list')

    class Meta:
        ordering = ('status', '-modified')
        unique_together = ('requesting_user', 'requested_user')
        

class Location(models.Model):
    country = models.CharField(max_length=40)
    state = models.CharField(max_length=40, null=True, blank=True)
    county = models.CharField(max_length=40, null=True, blank=True)
    city = models.CharField(max_length=40, null=True, blank=True)
    components = ['country', 'state', 'county', 'city']

    class Meta:
        verbose_name_plural = 'Orte'
        verbose_name = 'Ort'
        unique_together = [['country', 'state', 'county', 'city']]

    def as_dict(self):
        return {_('Land'): self.country,
                _('Bundesland'): self.state,
                _('Landkreis'): self.county,
                _('Stadt'): self.city}

    def __str__(self):
        return self.city + ", " + self.state

    def full_address(self):
        return self.country + ", " + self.state + (", " + self.county if self.county else "") + ", " + self.city
        
    def chat_allowed_for(self, user):
        return user.location == self

    @staticmethod
    def get_from_location(location: geopy.location.Location):
        address = location.raw['address']
        location, created = Location.objects.get_or_create(
            country=address['country'],
            state=address.get('state', address.get('city', address.get('town'))),
            county=address.get('county'),
            city=address.get('city', address.get('town')))
        return location

    def get_component(self, component):
        if component == 'country':
            return self.country
        elif component == 'state':
            return self.state
        elif component == 'county':
            return self.county
        else:
            return self.city

    def get_components(self, components):
        return [str(self.get_component(component)) + " " for component in components]

    def equal_to(self, location, granularity):
        i = Location.components.index(granularity)
        components = Location.components[:i + 1]
        return self.get_components(components) == location.get_components(components)
