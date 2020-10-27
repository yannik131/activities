from django.shortcuts import render
from activity.models import Activity
from account.models import Location, User
from . import utils
from .forms import MatchForm, TournamentForm, AddUserToTournamentForm
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponseServerError
from .models import Match, Tournament, Round
from shared import shared
from django.utils import timezone
import datetime


def user_overview(request):
    return render(request, 'competitions/user_overview.html')


def overview(request, activity_id):
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
    activity = Activity.objects.get(id=activity_id)
    matches = Match.objects.filter(activity=activity, public=True)
    component = Location.components[component_index]
    matches = [match for match in matches.all() if match.vacancies.count() and match.location.equal_to(request.user.location, component)]
    tournaments = Tournament.objects.filter(activity=activity)
    tournaments = [tournament for tournament in tournaments.all() if tournament.location.equal_to(request.user.location, component)]
    return render(request, 'competitions/overview.html', dict(activity=activity, component_index=component_index, chosen_component=chosen_component, matches=matches, tournaments=tournaments))


def create_match(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    if request.method == 'POST':
        form = MatchForm(request.POST)
        form.instance.activity = activity
        form.instance.admin = request.user
        if form.is_valid():
            match = form.save()
            return HttpResponseRedirect(match.get_absolute_url())
    else:
        form = MatchForm(initial=dict(location=request.user.location.get_component('city')))
    return render(request, 'competitions/create_match.html', dict(form=form, activity=activity))


def edit_match(request, match_id):
    match = Match.objects.get(id=match_id)
    if request.method == 'POST':
        form = MatchForm(request.POST, instance=match)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(match.get_absolute_url())
    else:
        form = MatchForm(instance=match, initial=dict(location=match.location.get_component('city')))
    return render(request, 'competitions/edit_match.html', dict(form=form, match=match))


def delete_match(request, match_id):
    match = Match.objects.get(id=match_id)
    if request.user != match.admin:
        return HttpResponseForbidden()
    match.delete()
    return HttpResponseRedirect(match.activity.get_absolute_url())


def match_detail(request, match_id):
    match = Match.objects.get(id=match_id)
    return render(request, 'competitions/match_detail.html', dict(match=match, is_member=request.user in match.members.all()))


def create_tournament(request, activity_id):
    activity = Activity.objects.get(id=activity_id)
    if request.method == 'POST':
        form = TournamentForm(request.POST)
        if form.is_valid():
            form.instance.admin = request.user
            form.instance.activity = activity
            tournament = form.save()
            return HttpResponseRedirect(tournament.get_absolute_url())
    else:
        form = TournamentForm(initial=dict(
            title=str(activity)+"-Turnier",
            location=request.user.location.get_component('city'),
            starting_time=(timezone.now()+datetime.timedelta(days=7)).strftime(shared.GERMAN_DATE_FMT),
            application_deadline=(timezone.now()+datetime.timedelta(days=6)).strftime(shared.GERMAN_DATE_FMT)))
    return render(request, 'competitions/create_tournament.html', dict(form=form, activity=activity))


def edit_tournament(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    if request.user != tournament.admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = TournamentForm(request.POST, instance=tournament)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(tournament.get_absolute_url())
    else:
        form = TournamentForm(instance=tournament, initial=dict(location=tournament.location.get_component('city')))
    return render(request, 'competitions/edit_tournament.html', dict(form=form, tournament=tournament))


def delete_tournament(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    if tournament.admin != request.user:
        return HttpResponseForbidden()
    tournament.delete()
    return HttpResponseRedirect(tournament.activity.get_absolute_url())


def tournament_detail(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    return render(request, 'competitions/tournament_detail.html', dict(tournament=tournament))


def add_tournament_member(request, tournament_id, user_id):
    tournament = Tournament.objects.get(id=tournament_id)
    if request.user != tournament.admin:
        return HttpResponseForbidden()
    user = User.objects.get(id=user_id)
    tournament.members.add(user)
    return HttpResponseRedirect(request.build_absolute_uri(f"/competitions/edit_tournament/{tournament.id}"))


def remove_tournament_member(request, tournament_id, user_id, who):
    tournament = Tournament.objects.get(id=tournament_id)
    if who == 'admin':
        if request.user != tournament.admin:
            return HttpResponseForbidden()
        user = User.objects.get(id=user_id)
        tournament.members.remove(user)
        return HttpResponseRedirect(request.build_absolute_uri(f"/competitions/edit_tournament/{tournament.id}"))
    elif who == 'user':
        user = User.objects.get(id=user_id)
        if request.user != user:
            return HttpResponseForbidden()
        tournament.members.remove(user)
        return HttpResponseRedirect(tournament.get_absolute_url())


def tournament_standings(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    players = utils.sorted_player_list(tournament.points, tournament.tie_breaks)
    players = [(User.objects.get(id=int(k)), s, t) for k, s, t in players]
    return render(request, 'competitions/full_table.html', dict(tournament=tournament, players=players))


def game_plan(request, tournament_id, round_number):
    tournament = Tournament.objects.get(id=tournament_id)
    try:
        round = tournament.rounds.get(number=round_number)
    except Round.DoesNotExist:
        return HttpResponseRedirect(tournament.get_absolute_url())
    return render(request, 'competitions/game_plan.html', dict(tournament=tournament, round=round))


def generate_next_round(request, tournament_id):
    tournament = Tournament.objects.get(id=tournament_id)
    if request.user != tournament.admin:
        return HttpResponseForbidden()
    n = 1
    if tournament.rounds.all().exists():
        last_round = tournament.rounds.all().last()
        if not last_round.over:
            return HttpResponseServerError('Es stehen noch Ergebnisse der letzten Runde offen.')
        n = last_round.number+1
    round = Round.objects.create(tournament=tournament, number=n)

    return render(request, 'competitions/game_plan.html', dict(tournament=tournament, round=round))

