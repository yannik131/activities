from django import template
from itertools import chain
from shared.shared import n_parenthesis

register = template.Library()


@register.simple_tag
def changed_requests(user):
    request_list = list(chain(user.sent_friend_requests.all(), user.received_friend_requests.all()))
    return [r for r in request_list if r.modified > user.latest_request_check]


@register.simple_tag
def new_request_number_string(user):
    number = len(changed_requests(user))
    return n_parenthesis(number)
