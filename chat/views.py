from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect
from .templatetags import chat_tags
from django.utils import timezone
from .models import ChatRoom


@login_required
def chat_room(request, app_label, model, id):
    try:
        chat_room = ChatRoom.get(app_label, model, id)
    except:
        return HttpResponseForbidden('Diesen Chat-Room gibt es nicht mehr.')
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
    return render(request, 'chat/chat_list.html', dict(new_messages=new_messages))
