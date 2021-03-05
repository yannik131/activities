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
    match = None
    if activity.name == _("Skat"):
        match = MultiplayerMatch.objects.create(activity=activity, member_limit=3, admin=request.user)
    elif activity.name == _("Doppelkopf"):
        match = MultiplayerMatch.objects.create(activity=activity, member_limit=4, admin=request.user)
    if request.method == 'POST':
        form = CreateMatchForm(request.POST)
        form.activity = activity
        if form.is_valid():
            match = form.save(commit=False)
            match.activity = activity
            match.admin = request.user
            match.save()
    else:
        form = CreateMatchForm()
    if match:
        match.init_positions()
        match.members.add(match.admin)
        return HttpResponseRedirect(match.get_absolute_url())
    return render(request, 'multiplayer/create_match.html', dict(activity=activity, form=form))


@guard_match
def match(request, match):
    is_member = match.members.filter(pk=request.user.id).exists()
    if not is_member:
        return HttpResponseRedirect(match.lobby_url(request))
    members = sorted([(User.objects.get(id=v), k) if v else ("", k) for k, v in match.member_positions.items()], key=lambda t: t[1])
    while len(members) < 4:
        members.append(("", len(members)))
    
    if is_member and match.in_progress:
        return HttpResponseRedirect(request.build_absolute_uri(f"/multiplayer/game/{match.activity.name}/{match.id}/"))
    elif match.is_full() and match.in_progress:
        messages.add_message(request, messages.INFO, _("Spiel ist bereits voll"))
        return HttpResponseRedirect(match.lobby_url(request))
    return render(request, 'multiplayer/match.html', dict(match=match, members=members, is_member=is_member, room=ChatRoom.get_for_target(match)))
    
@guard_match
def start_match(request, match):
    if not match.is_full():
        return HttpResponseRedirect(match.get_absolute_url())
    match.start()
    return HttpResponseRedirect(match.get_absolute_url())

@guard_match
def enter_match(request, match):
    if request.user in match.members.all():
        return HttpResponseRedirect(match.get_absolute_url())
    elif match.is_full():
        messages.add_message(request, messages.INFO, _("Sie waren zu langsam, das Match war bereits voll."))
        return HttpResponseRedirect(match.lobby_url(request))
    match.add_member(request.user)
    return HttpResponseRedirect(match.get_absolute_url())
    
    

@guard_match
def leave_match(request, match):
    if not match.members.filter(pk=request.user.id).exists():
        return HttpResponseRedirect(match.lobby_url(request))
    if match.admin == request.user:
        match.abort(redirect_to_lobby=True)
        match.delete()
        return HttpResponseRedirect(match.lobby_url(request))
    match.remove_member(request.user)
    return HttpResponseRedirect(match.lobby_url(request))


@guard_match
def game(request, match):
    if not match.is_full():
        return HttpResponseRedirect(match.get_absolute_url())
    data = dict(match=match, room=ChatRoom.get_for_target(match))
    if match.activity.name == _('Durak'):
        return render(request, 'multiplayer/durak.html', data)
    elif match.activity.name == _("Skat"):
        return render(request, 'multiplayer/skat.html', data)
    elif match.activity.name == _("Doppelkopf"):
        return render(request, 'multiplayer/doppelkopf.html', data)
    return HttpResponseNotFound()
        
