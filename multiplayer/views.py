from django.shortcuts import render, get_object_or_404
from .models import MultiplayerMatch
from .forms import CreateMatchForm
from activity.models import Activity
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseServerError
from django.utils.translation import gettext_lazy as _
import json
from chat.models import ChatRoom
from django.contrib import messages
from account.models import User


def lobby(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    return render(request, 'multiplayer/lobby.html', dict(activity=activity))


def create_match(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
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


def match(request, match_id):
    match = get_object_or_404(MultiplayerMatch, id=match_id)
    members = [(User.objects.get(id=v), k) if v else (None, k) for k, v in match.member_positions.items()]
    is_member = match.members.filter(pk=request.user.id).exists()
    return render(request, 'multiplayer/match.html', dict(match=match, members=members, is_member=is_member))
    
    
def enter_match(request, match_id):
    match = MultiplayerMatch.objects.get(id=match_id)
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
    
    
def leave_match(request, match_id):
    match = MultiplayerMatch.objects.get(pk=match_id)
    if not match.members.filter(pk=request.user.id).exists():
        return HttpResponseServerError()
    if match.members.all().count() == 1:
        match.delete()
    else:
        room = ChatRoom.get_for_target(match)
        room.members.remove(request.user)
        match.members.remove(request.user)
        for k, v in match.member_positions.items():
            if v == str(request.user.id):
                match.member_positions[k] = None
                match.save()
                break
    return HttpResponseRedirect(match.lobby_url(request))


def game(request, match_id):
    match = MultiplayerMatch.objects.get(id=match_id)
    if match.activity.name == _('Durak'):
        return render(request, 'multiplayer/durak.html')
        

def get_online_list(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    members = [user.username for user in activity.members.exclude(channel_name__isnull=True)]
    matches = [[match.members.all().count(), match.member_limit, match.id] for match in activity.multiplayer_matches.all() if match.members.all().count() != match.member_limit]
    data = dict(members=members, matches=matches)
    return HttpResponse(json.dumps(data))
