from django import template
from itertools import chain
from shared.shared import n_parenthesis
from django.utils.safestring import mark_safe
from activities.language_subdomain_middleware import get_prefix
from account.models import User

register = template.Library()


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

SECTIONS = {
    'home': ['/account/'],
    'activities': ['/activity/list', '/activity/detail'],
    'categories': ['/activity/category'],
    'competitions': ['/multiplayer', '/competitions'],
    'groups': ['/usergroups'],
    'chat': ['/chat'],
    'vacancies': ['/vacancies'],
    'friends': ['/account/friend'],
    'account': ['/account/edit', '/account/password_change', '/account/delete'],
    'character': ['/character']
}

@register.simple_tag
def active_if(request, section):
    okay = mark_safe('class="active"')
    path = request.path
    if section == 'home':
        if path == SECTIONS['home'][0]:
            return okay
        return ""
    for p in SECTIONS[section]:
        if path.startswith(p):
            return okay
    return ""
    
    
@register.simple_tag
def language_setter(request):
    language = get_prefix(request)
    if language == "de":
        return mark_safe(f"<a href='https://en.myactivities.net{request.path}'>EN</a>")
    return mark_safe(f"<a href='https://myactivities.net{request.path}'>DE</a>")
    

@register.simple_tag
def online_count():
    return User.objects.filter(channel_name__isnull=False).count()
    

@register.simple_tag
def total_count():
    return User.objects.count()