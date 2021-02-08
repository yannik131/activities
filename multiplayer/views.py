from django.http.response import HttpResponseNotFound
from shared.shared import log
from django.shortcuts import render, get_object_or_404
from .models import MultiplayerMatch
from .forms import CreateMatchForm
from activity.models import Activity
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.utils.translation import gettext_lazy as _
from chat.models import ChatRoom
from django.contrib import messages
from account.models import User
from .decorators import guard_match


def lobby(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    online_list = activity.members.filter(channel_name__isnull=False)
    user_matches = request.user.multiplayer_matches.filter(activity__id=activity.id)
    return render(request, 'multiplayer/lobby.html', dict(activity=activity, online_list=online_list, user_matches=user_matches))


def create_match(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    if activity.name == _("Skat"):
        match = MultiplayerMatch.objects.create(activity=activity, member_limit=3)
        match.add_first_member(request.user)
        return HttpResponseRedirect(match.get_absolute_url())
    elif activity.name == _("Doppelkopf"):
        match = MultiplayerMatch.objects.create(activity=activity, member_limit=4)
        match.add_first_member(request.user)
        return HttpResponseRedirect(match.get_absolute_url())
    if request.method == 'POST':
        form = CreateMatchForm(request.POST)
        form.activity = activity
        if form.is_valid():
            match = form.save(commit=False)
            match.activity = activity
            for i in range(1, match.member_limit+1):
                match.member_positions[str(i)] = None
            match.member_positions['1'] = str(request.user.id)
            match.save()
            match.members.add(request.user)
            return HttpResponseRedirect(match.get_absolute_url())
    else:
        form = CreateMatchForm()
    return render(request, 'multiplayer/create_match.html', dict(activity=activity, form=form))


@guard_match
def match(request, match):
    members = [(User.objects.get(id=v), k) if v else (None, k) for k, v in match.member_positions.items()]
    is_member = match.members.filter(pk=request.user.id).exists()
    if is_member and match.is_full():
        return HttpResponseRedirect(request.build_absolute_uri(f"/multiplayer/game/{match.activity.name}/{match.id}/"))
    elif match.is_full():
        messages.add_message(request, messages.INFO, _("Spiel ist bereits voll"))
        return HttpResponseRedirect(match.lobby_url(request))
    return render(request, 'multiplayer/match.html', dict(match=match, members=members, is_member=is_member))
    

@guard_match
def enter_match(request, match):
    if request.user in match.members.all():
        return HttpResponseServerError()
    for k, v in match.member_positions.items():
        if v is None:
            match.member_positions[k] = str(request.user.id)
            match.save()
            match.members.add(request.user)
            room = ChatRoom.get_for_target(match)
            if request.user not in room.members.all():
                room.members.add(request.user)
            return HttpResponseRedirect(match.get_absolute_url())
    messages.add_message(request, messages.INFO, _("Sie waren zu langsam, das Match war bereits voll."))
    return HttpResponseRedirect(match.lobby_url(request))
    

@guard_match
def leave_match(request, match):
    if not match.members.filter(pk=request.user.id).exists():
        return HttpResponseRedirect(match.lobby_url(request))
    if match.member_positions['1'] == str(request.user.id):
        match.abort(redirect_to_lobby=True)
        match.delete()
        return HttpResponseRedirect(match.lobby_url(request))
    room = ChatRoom.get_for_target(match)
    room.members.remove(request.user)
    match.members.remove(request.user)
    for k, v in match.member_positions.items():
        if v == str(request.user.id):
            match.member_positions[k] = None
            match.save()
            break
    if match.in_progress:
        match.abort()
    return HttpResponseRedirect(match.lobby_url(request))


@guard_match
def game(request, match):
    if not match.is_full():
        return HttpResponseRedirect(match.get_absolute_url())
    if match.activity.name == _('Durak'):
        return render(request, 'multiplayer/durak.html', dict(match=match))
    elif match.activity.name == _("Skat"):
        return render(request, 'multiplayer/skat.html', dict(match=match))
    elif match.activity.name == _("Doppelkopf"):
        return render(request, 'multiplayer/doppelkopf.html', dict(match=match))
    return HttpResponseNotFound()
        
