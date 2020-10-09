from django import template
from vacancies.models import Invitation
from account.models import User

register = template.Library()


@register.simple_tag
def invitation_number_string(user):
    n = Invitation.objects.filter(target_id=user.id, target_ct=User.content_type()).count()
    if n:
        return f' ({n})'
    return ''
