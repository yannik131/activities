import magic
from geopy.geocoders import Nominatim
from django.forms import ValidationError
from account.models import Location
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseNotFound


def paginate(object_list, request, limit=3):
    paginator = Paginator(object_list, limit)
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
    return objects, page


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


def add(d, key, value):
    d[key] = str(int(d[key])+int(value))


def slashify(path):
    if not path.startswith('/'):
        path = '/' + path
    if not path.endswith('/'):
        path = path + '/'
    return path


def log(*args):
    with open('log.log', 'a') as file:
        file.write(now().strftime("%Y-%m-%d %H:%M:%S") + ": ")
        for arg in args:
            file.write(str(arg) + " ")
        file.write("\n")
        

def redirect_before_or_404(request):
    if "HTTP_REFERER" in request.META:
        return request.META['HTTP_REFERER']
    return HttpResponseNotFound()


GERMAN_DATE_FMT = '%d.%m.%Y %H:%M'
