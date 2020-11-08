from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .templatetags import chat_tags
from account.models import Friendship
from usergroups.models import UserGroup
from competitions.models import Match, Tournament
from .models import ChatRoom
from django.utils.translation import gettext_lazy as _


@login_required
def chat_room(request, app_label, model, id):
    try:
        chat_room = ChatRoom.get(app_label, model, id)
    except:
        return HttpResponseForbidden(_('Diesen Chat-Room gibt es nicht mehr.'))
    if chat_room.is_allowed_here(request.user):
        if request.user not in chat_room.members.all():
            chat_room.members.add(request.user)
    else:
        return HttpResponseForbidden()
    return render(request, 'chat/room.html', dict(target=chat_room.target, room=chat_room))


@login_required
def chat_list(request):
    new_messages = chat_tags.new_messages_dict(request.user)
    request.user.save()
    chat_rooms = request.user.chat_rooms.all()
    group_rooms = []
    friend_rooms = []
    match_rooms = []
    tournament_rooms = []
    for room in chat_rooms:
        if type(room.target) is UserGroup:
            group_rooms.append(room)
        elif type(room.target) is Friendship:
            friend_rooms.append(room)
        elif type(room.target) is Match:
            match_rooms.append(room)
        elif type(room.target) is Tournament:
            tournament_rooms.append(room)
    return render(request, 'chat/chat_list.html', dict(new_messages=new_messages, group_rooms=group_rooms, friend_rooms=friend_rooms, match_rooms=match_rooms, tournament_rooms=tournament_rooms))
