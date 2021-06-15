from datetime import time
from notify.models import Notification
from activity.models import Activity
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.query import QuerySet
import geopy
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from itertools import chain
from django.utils.translation import gettext_lazy as _
from character.models import Character
from .utils import geocode
from django.forms import ValidationError
from shared.shared import log
import json

class User(AbstractUser):
    profile_text = models.TextField(null=True, blank=True)
    image = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True)
    location = models.ForeignKey("Location", on_delete=models.CASCADE, blank=True, related_name='population')
    latest_request_check = models.DateTimeField(default=timezone.now)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    SEX_CHOICES = (
        ('m', _('männlich')),
        ('w', _('weiblich'))
    )
    sex = models.CharField(max_length=1, choices=SEX_CHOICES, null=True, blank=True)
    confirmed_appointments = models.ManyToManyField("scheduling.Appointment", related_name='participants')
    cancelled_appointments = models.ManyToManyField("scheduling.Appointment", related_name='cancellations')
    channel_name = models.CharField(max_length=100, null=True)
    character = models.OneToOneField(Character, on_delete=models.SET_NULL, null=True, related_name='user')
    last_location_change = models.DateTimeField(null=True, blank=True)
    audio_room_id = models.PositiveIntegerField(null=True)
    LOCATION_CHANGE_DAYS = 7
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
        'posted': _('hat etwas gepostet'),
        'commented_in': _('hat etwas kommentiert'),
        'terminated_friendship': _('hat eure Freundschaft beendet'),
        'invited': _('hat Sie eingeladen'),
        'accepted_friend_request': _('hat Ihre Freundschaftsanfrage angenommen'),
        'declined_friend_request': _('hat Ihre Freundschaftsanfrage abgelehnt'),
        'declined_application': _('hat Ihre Bewerbung abgelehnt'),
        'likes': _('gefällt'),
        'dislikes': _('missfällt')
    }
            
    @property
    def age(self):
        if self.birth_year:
            return timezone.now().year - self.birth_year
        return None
    
    @property
    def get_image(self):
        if self.image:
            return self.image
        elif self.sex == 'm':
            return 'static/icons/male_user.png'
        elif self.sex == 'w':
            return 'static/icons/female_user.png'
        else:
            return 'static/icons/male_female_user.png'
    
    def friendships(self):
        return list(chain(self.from_friendships.all(), self.to_friendships.all()))

    def get_friendship_for(self, user):
        return next((friendship for friendship in self.friendships() if friendship.to_user == user or friendship.from_user == user), None)

    def friends(self):
        return [f.get_other_user(self) for f in self.friendships()]

    def get_latest_messages(self):
        chat_checks = self.last_chat_checks.prefetch_related('room', 'room__log_entries').all()
        rooms = {}
        for check in chat_checks:
            messages = check.new_messages()
            if messages:
                rooms[check.room.id] = '1'
        return json.dumps(rooms)
        
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
    def ws_key(self):
        return str(hash((self.last_login, self.date_joined)))
        
    @property
    def channel_group_name(self):
        return f"user-{self.id}"
        
    @property
    def get_notifications(self):
        notifications = []
        for notification in self.notifications.all():
            if notification.should_be_deleted or len(notifications) >= Notification.MAXIMUM:
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
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    parent = models.ForeignKey('Location', null=True, on_delete=models.SET_NULL, related_name='children')
    
    components = ['country', 'state', 'county', 'city']

    class Meta:
        verbose_name_plural = 'Orte'
        verbose_name = 'Ort'
        unique_together = ['country', 'state', 'county', 'city']
        indexes = [
            models.Index(fields=['country', 'state', 'county', 'city'])
        ]
        
    @property
    def get_image(self):
        return 'static/icons/location.png'
      
    @staticmethod
    def determine_from(address):
        try:
            if ',' in address:
                city, state = address.split(',')
                city = city.lstrip().title()
                state = state.lstrip().title()
                location = Location.objects.get(city=city, state=state)
            else:
                location = Location.objects.get(city=address.lstrip().title())
            return location
        except:
            pass
        location = geocode(address, addressdetails=True)
        if location is None:
            raise ValidationError(_('Diese Adresse konnte nicht gefunden werden.'))
        elif not any(key in location.raw['address'] for key in ['city', 'town', 'village']):
            raise ValidationError(_('Aus der Adresse konnte die Stadt nicht ermittelt werden. Bitte geben Sie die Stadt explizit an (Dörfer/Ortsteile werden nicht erkannt).'))
        else:
            return Location.get_from_geopy_location(location)    
    
    @staticmethod
    def fill_coordinates():
        l = [l for l in Location.objects.all()]
        for loc in l:
            print(loc)
            location = geocode(str(loc), addressdetails=True)
            if not location:
                print(f'Not found: {loc}')
                continue
            loc.longitude = round(location.longitude, 6)
            loc.latitude = round(location.latitude, 6)
            loc.save()
            
    @staticmethod
    def get_or_create(components, longitude, latitude):
        try:
            location = Location.objects.get(**components)
        except:
            location = Location.objects.create(**components, latitude=round(latitude, 6), longitude=round(longitude, 6))
        return location
            
    @staticmethod
    def get_from_geopy_location(location: geopy.location.Location):
        address = location.raw['address']
        components = dict(
            country=address['country'],
            state=address.get('state', address.get('city', address.get('town'))),
            county=address.get('county'),
            city=address.get('city', address.get('town', address.get('village')))
        )
        return Location.get_or_create(components, location.longitude, location.latitude)
        
    @staticmethod
    def get(country=None, state=None, county=None, city=None):
        return Location.objects.get(country=country, state=state, county=county, city=city)
        
    @staticmethod
    def filter(country=None, state=None, county=None, city=None):
        return Location.objects.filter(country=country, state=state, county=county, city=city)
            
    def highest_component_index(self):
        for i, element in enumerate(reversed(Location.components)):
            if getattr(self, element):
                return 3-i
            
    def get_population(self, users: QuerySet):
        if self.city:
            return self.population.all()
        for element in reversed(Location.components[:-1]):
            if getattr(self, element):
                return users.filter(**{'location__'+element: getattr(self, element)})

    def as_dict(self):
        return {_('Land'): self.country,
                _('Bundesland'): self.state,
                _('Landkreis'): self.county,
                _('Stadt'): self.city}

    def __str__(self):
        if self.city:
            return self.city + ", " + self.state
        elif self.county:
            return self.county + ", " + self.state
        elif self.state:
            return self.state + ", " + self.country
        else:
            return self.country

    def full_address(self):
        return self.country + ", " + self.state + (", " + self.county if self.county else "") + ", " + self.city
        
    def chat_allowed_for(self, user):
        return user.location == self
        
    def get_parent(self, index):
        attrs = dict([(component, getattr(self, component)) for component in Location.components[:index+1]])
        return Location.get(**attrs)
            
    def parent_components(self):
        return dict([(component, getattr(self, component)) for component in Location.components[:self.highest_component_index()] if getattr(self, component)])

    def get_components(self, components):
        return [str(getattr(self, component)) + " " for component in components]

    def equal_to(self, location, granularity):
        i = Location.components.index(granularity)
        components = Location.components[:i + 1]
        return self.get_components(components) == location.get_components(components)

class LocationMarker(models.Model):
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='markers')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='markers')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='markers', null=True)
    description = models.CharField(max_length=100)
    
