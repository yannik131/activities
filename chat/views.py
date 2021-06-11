from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from account.views import handler404, handler403
from .models import ChatRoom


def chat_room(request, app_label, model, id):
    try:
        chat_room = ChatRoom.get(app_label, model, id)
    except:
        return handler404(request, _('Diesen Chat-Room gibt es nicht mehr.'))
    if chat_room.is_allowed_here(request.user):
        if request.user not in chat_room.members.all():
            chat_room.members.add(request.user)
    else:
        return handler403(request)
    request.user.last_chat_checks.filter(room=chat_room).update(date=timezone.now())
    return render(request, 'chat/room.html', dict(room=chat_room, current_chat_room=chat_room, friendship=model == 'friendship'))
