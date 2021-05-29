from shared.shared import log
from django.shortcuts import render, get_object_or_404
from .models import MultiplayerMatch
from .forms import *
from activity.models import Activity
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _
from chat.models import ChatRoom
from django.contrib import messages
from account.models import User
from .decorators import guard_match
from django.urls import reverse


def lobby(request, activity_name, extra=None):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    if extra == 'guarded' and not request.user.activities.filter(pk=activity.id).exists():
        activity.members.add(request.user)
        messages.add_message(request, messages.INFO, _('Sie sind der Aktivität {name} beigetreten.').format(name=activity.name))
    elif extra == 'kicked':
        messages.add_message(request, messages.INFO, _('Sie wurden aus dem Spiel gekickt. Bitte treten Sie nur wieder bei, wenn Sie sich sicher sind, dass das ein Versehen war.'))
    online_list = activity.members.filter(channel_name__isnull=False)
    user_matches = request.user.multiplayer_matches.filter(activity__id=activity.id)
    room = ChatRoom.get_for_target(activity)
    return render(request, 'multiplayer/lobby.html', dict(activity=activity, online_list=online_list, user_matches=user_matches, current_chat_room=room))


def create_match(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    if request.user.admin_matches.filter(activity=activity).count() > MultiplayerMatch.MAX_INSTANCES:
        messages.add_message(request, messages.INFO, _('Sie können nicht mehr als {n} Matches erstellen.').format(n=MultiplayerMatch.MAX_INSTANCES))
        return HttpResponseRedirect(reverse('multiplayer:lobby', args=[activity]))
    match = None
    name = activity.german_name
    if name == "Skat":
        match = MultiplayerMatch.objects.create(activity=activity, member_limit=3, admin=request.user)
    if request.method == 'POST':
        if name == 'Poker':
            form = PokerMatchForm(request.POST)
        elif name == 'Doppelkopf':
            form = DokoMatchForm(request.POST)
        elif name =='Durak':
            form = DurakMatchForm(request.POST)
        else:
            form = CreateMatchForm(request.POST)
        form.activity = activity
        if form.is_valid():
            match = form.save(commit=False)
            match.activity = activity
            match.admin = request.user
            if name == 'Poker':
                match.options['blind_duration'] = form.cleaned_data['blind_duration']
            elif name == 'Doppelkopf':
                match.options['without_nines'] = form.cleaned_data['without_nines']
            elif name == 'Durak':
                match.options['all_help'] = form.cleaned_data['all_help']
            match.save() 
    else:
        if name == 'Poker':
            form = PokerMatchForm()
        elif name == 'Doppelkopf':
            form = DokoMatchForm(initial={'member_limit': 4})
        elif name == 'Durak':
            form = DurakMatchForm()
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
    members = sorted([(v, k) if v else ("", k) for k, v in match.member_positions.items()], key=lambda t: t[1])
    while len(members) < 4:
        members.append(("", len(members)))
    
    if is_member:
        if match.in_progress:
            return HttpResponseRedirect(request.build_absolute_uri(f"/multiplayer/game/{match.activity.name}/{match.id}/"))
    elif match.is_full():
        messages.add_message(request, messages.INFO, _("Spiel ist bereits voll"))
        return HttpResponseRedirect(match.lobby_url(request))
    return render(request, 'multiplayer/match.html', dict(match=match, members=members, is_member=is_member, current_chat_room=ChatRoom.get_for_target(match)))


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
        match.delete()
        return HttpResponseRedirect(match.lobby_url(request))
    match.remove_member(request.user)
    return HttpResponseRedirect(match.lobby_url(request))


@guard_match
def game(request, match):
    if not match.in_progress:
        return HttpResponseRedirect(match.get_absolute_url())
    data = dict(match=match, current_chat_room=ChatRoom.get_for_target(match))
    return render(request, 'multiplayer/game.html', data)
    

def rules(request):
    return render(request, 'multiplayer/rules.html')
