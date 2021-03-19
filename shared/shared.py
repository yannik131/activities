import magic
from geopy.geocoders import Nominatim
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import HttpResponseNotFound
from datetime import timedelta


def paginate(object_list, request, limit=3):
    paginator = Paginator(object_list, limit)
    page = request.GET.get('page')
    try:
        objects = paginator.page(page)
    except PageNotAnInteger:
        objects = paginator.page(1)
        page = 1
    except EmptyPage:
        objects = paginator.page(paginator.num_pages)
        page = paginator.num_pages
    return objects, page


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
    
def long_ago():
    return now()-timedelta(weeks=1000)


GERMAN_DATE_FMT = '%d.%m.%Y %H:%M'
