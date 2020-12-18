from django import template
from shared.shared import n_parenthesis

register = template.Library()


@register.simple_tag
def chat_star(messages, room_id):
    for log_entry in messages:
        if log_entry.chat_room.id == room_id:
            return '*'
    return ''
