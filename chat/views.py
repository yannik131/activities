from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .templatetags import chat_tags
from account.models import Friendship
from usergroups.models import UserGroup
from competitions.models import Match, Tournament
from .models import ChatRoom, ChatCheck
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from account.views import handler403


@login_required
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


@login_required
def chat_list(request):
    request.user.save()
    chat_rooms = request.user.chat_rooms.all()
    group_rooms = []
    friend_rooms = []
    match_rooms = []
    tournament_rooms = []
    for room in chat_rooms:
        if type(room.target) is UserGroup:
            group_rooms.append((room, room.target))
        elif type(room.target) is Friendship:
            friend_rooms.append((room, room.target.get_other_user(request.user)))
        elif type(room.target) is Match:
            match_rooms.append((room, room.target))
        elif type(room.target) is Tournament:
            tournament_rooms.append((room, room.target))

    def key(t):
        return t[0].title_for(request.user)

    return render(request, 'chat/chat_list.html', dict( group_rooms=sorted(group_rooms, key=key), friend_rooms=sorted(friend_rooms, key=key), match_rooms=sorted(match_rooms, key=key), tournament_rooms=sorted(tournament_rooms, key=key)))
