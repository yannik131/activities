from django import template
from itertools import chain
from shared.shared import n_parenthesis
from django.utils.safestring import mark_safe
from activities.language_subdomain_middleware import get_prefix
from account.models import User
from activity.models import Activity, Category
import random
from easy_thumbnails.files import get_thumbnailer

register = template.Library()

@register.filter
def rand_inc(n):
    return n+random.randint(0, 2)

@register.simple_tag
def call_method(obj, function_name, *args):
    function = getattr(obj, function_name)
    return function(*args)

@register.simple_tag
def changed_requests(user):
    request_list = list(chain(user.sent_friend_requests.all(), user.received_friend_requests.all()))
    return [r for r in request_list if r.modified > user.latest_request_check]

@register.simple_tag
def new_request_number_string(user):
    number = len(changed_requests(user))
    return n_parenthesis(number)
    
    
@register.simple_tag
def language_setter(request):
    language = get_prefix(request)
    if language == "de":
        return mark_safe(f"<a href='https://en.myactivities.net{request.path}'>EN</a>")
    return mark_safe(f"<a href='https://de.myactivities.net{request.path}'>DE</a>")
    

@register.simple_tag
def online_count():
    return User.objects.filter(channel_name__isnull=False).count()
    

@register.simple_tag
def total_count():
    return User.objects.filter(is_active=True).count()

@register.simple_tag
def activity_image(name, size_in_pixels=400):
    activity = Activity.objects.get(translations__language_code='en', translations__name=name)
    return get_thumbnailer(activity.image).get_thumbnail(dict(size=(size_in_pixels, size_in_pixels))).url
    
@register.simple_tag
def category_image(name, size_in_pixels=400):
    category = Category.objects.get(translations__language_code='en', translations__name=name)
    return get_thumbnailer(category.image).get_thumbnail(dict(size=(size_in_pixels, size_in_pixels))).url