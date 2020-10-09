from django import template
from shared.shared import n_parenthesis

register = template.Library()


@register.simple_tag
def new_messages_dict(user):
    room_ids = user.chat_rooms.values_list('id', flat=True)
    messages = dict.fromkeys(room_ids)
    for room in user.chat_rooms.all():
        messages[room.id] = user.last_chat_checks.get(room=room).new_messages().count()
    return messages


@register.simple_tag
def new_messages_str(user):
    messages = new_messages_dict(user)
    n = sum([v for k, v in messages.items()])
    return n_parenthesis(n)
