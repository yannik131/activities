from .models import MultiplayerMatch
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _


def guard_match(func):
    def wrapper(request, activity_name, match_id, *args):
        match = MultiplayerMatch.objects.filter(pk=match_id)
        if not match.exists():
            messages.add_message(request, messages.INFO, _('Das Spiel existiert nicht mehr.'))
            return HttpResponseRedirect(f"/multiplayer/lobby/{activity_name}/")
        match = match.first()
        if match.in_progress and not match.members.filter(pk=request.user.pk).exists():
            messages.add_message(request, messages.INFO, _('Sie sind kein Mitglied dieses Spiels.'))
            return HttpResponseRedirect(f"/multiplayer/lobby/{activity_name}/")
        return func(request, match, *args)
    return wrapper