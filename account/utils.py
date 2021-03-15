from .models import Location
from geopy import Nominatim
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _


def get_location(address):
    try:
        location = Location.objects.get(city=address)
        return location
    except Location.DoesNotExist:
        pass
    geolocator = Nominatim(user_agent='activities')
    location = geolocator.geocode(address, addressdetails=True)
    if location is None:
        raise ValidationError(_('Diese Adresse konnte nicht gefunden werden.'))
    elif location.raw['address'].get('city', location.raw['address'].get('town')) is None:
        raise ValidationError(_('Aus der Adresse konnte die Stadt nicht ermittelt werden. Bitte geben Sie die Stadt explizit an (Dörfer/Ortsteile werden nicht erkannt).'))
    else:
        return Location.get_from_location(location)