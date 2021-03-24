from django.shortcuts import render, get_object_or_404
from .templatetags import chat_tags
from account.models import Friendship
from usergroups.models import UserGroup
from competitions.models import Match, Tournament
from .models import ChatRoom, ChatCheck
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from account.views import handler403


def chat_room(request, app_label, model, id):
    try:
        chat_room = ChatRoom.get(app_label, model, id)
    except:
        return handler403(request, _('Diesen Chat-Room gibt es nicht mehr.'))
    if chat_room.is_allowed_here(request.user):
        if request.user not in chat_room.members.all():
            chat_room.members.add(request.user)
    else:
        return handler403(request)
    request.user.last_chat_checks.get(room=chat_room).update()
    return render(request, 'chat/room.html', dict(room=chat_room, friendship=model == 'friendship'))
