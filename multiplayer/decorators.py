from .models import MultiplayerMatch
from activity.models import Activity
from django.http import HttpResponseRedirect


def guard_match(func):
    def wrapper(request, activity_name, match_id):
        match = MultiplayerMatch.objects.filter(pk=match_id)
        if not match.exists():
            return HttpResponseRedirect(f"/multiplayer/lobby/{activity_name}/")
        return func(request, match.first())
    return wrapper