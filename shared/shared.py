import magic
from geopy.geocoders import Nominatim
from django.forms import ValidationError
from account.models import Location


def get_location(address):
    try:
        location = Location.objects.get(city=address)
        return location
    except Location.DoesNotExist:
        pass
    geolocator = Nominatim(user_agent='activities')
    location = geolocator.geocode(address, addressdetails=True)
    if location is None:
        raise ValidationError('Diese Adresse konnte nicht gefunden werden.')
    elif location.raw['address'].get('city') is None:
        raise ValidationError(
            'Aus der Adresse konnte die Stadt nicht ermittelt werden. Bitte geben Sie die Stadt explizit an (Dörfer/Ortsteile werden nicht erkannt).')
    else:
        return Location.get_from_location(location)


def xor_or_none(*args):
    result = sum([1 if arg else 0 for arg in args])
    return result == 1 or result == 0


def type_of(file):
    return magic.from_buffer(file.read(), mime=True)


def xor_get(iterable):
    for el in iterable:
        if el:
            return el
    return None


def n_parenthesis(n):
    if n:
        return f' ({n})'
    return ''


GERMAN_DATE_FMT = '%d.%m.%Y %H:%M'
