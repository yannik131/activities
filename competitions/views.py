from django.shortcuts import render
from activity.models import Activity
from account.models import Location, User
from .forms import MatchForm
from django.http import HttpResponseRedirect, HttpResponseForbidden
from .models import Match, Tournament


def user_overview(request):
    return render(request, 'competitions/user_overview.html')


def overview(request, activity_id):
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
    activity = Activity.objects.get(id=activity_id)
    matches = Match.objects.filter(activity=activity, public=True)
    component = Location.components[component_index]
    matches = [match for match in matches.all() if match.vacancies.count() and match.location.equal_to(request.user.location, component)]
    return render(request, 'competitions/overview.html', dict(activity=activity, component_index=component_index, chosen_component=chosen_component, matches=matches))


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
    return HttpResponseRedirect(request.build_absolute_uri('/competitions/user_overview/'))


def match_detail(request, match_id):
    match = Match.objects.get(id=match_id)
    return render(request, 'competitions/match_detail.html', dict(match=match, is_member=request.user in match.members.all()))
