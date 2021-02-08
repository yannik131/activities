from django import template
from itertools import chain
from shared.shared import n_parenthesis
from django.utils.safestring import mark_safe
from activities.language_subdomain_middleware import get_prefix

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


@register.simple_tag
def active_if(request, section):
    okay = mark_safe('class="active"')
    path = request.path
    if section == 'home':
        if path == '/account/':
            return okay
    elif section == 'activities':
        if path.startswith('/activity/list') or path.startswith('/activity/detail'):
            return okay
    elif section == 'categories':
        if path.startswith('/activity/category'):
            return okay
    elif section == 'competitions':
        if path.startswith('/competitions/'):
            return okay
    elif section == 'groups':
        if path.startswith('/usergroups/'):
            return okay
    elif section == 'chat':
        if path.startswith('/chat/'):
            return okay
    elif section == 'vacancies':
        if path.startswith('/vacancies/'):
            return okay
    elif section == 'friends':
        if path.startswith('/account/friend'):
            return okay
    elif section == 'password':
        if path.startswith('/account/password_change'):
            return okay
    elif section == 'account':
        if path.startswith('/account/edit'):
            return okay
    return ""
    
    
@register.simple_tag
def language_setter(request):
    language = get_prefix(request)
    if language == "de":
        return mark_safe(f"<a href='https://en.myactivities.net{request.path}'>EN</a>")
    return mark_safe(f"<a href='https://myactivities.net{request.path}'>DE</a>")
    
    
@register.simple_tag
def locale_picture(request, name):
    language = get_prefix(request)
    return mark_safe("{% static '"+name+"_"+language+".png' %}")