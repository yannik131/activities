from django.shortcuts import render
from activity.models import Activity
from account.models import Location


def overview(request, activity_id):
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
    activity = Activity.objects.get(id=activity_id)
    return render(request, 'competitions/overview.html', dict(activity=activity, component_index=component_index, chosen_component=chosen_component))


def create_match(request, activity_id):
    activity = Activity.objects.get(id=activity_id)


def delete_match(request, match_id):
    pass



