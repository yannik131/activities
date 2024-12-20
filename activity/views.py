from django.shortcuts import render
from .models import Activity, Category
from django.db.models import Count, Q
from account.models import Location, LocationMarker, User
from wall.models import Post
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from shared.shared import log, paginate
import json


def detail(request, activity_name):
    component_index = int(request.GET.get('component_index', 3))
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    is_member = request.user.activities.filter(pk=activity.id).exists()
    component = Location.components[component_index]
    chosen_component = getattr(request.user.location, component)
    users = activity.members.filter(**{'location__'+component: chosen_component})
    markers = []
    population = []
    
    if component_index == 3: # city
        markers.append([float(request.user.location.latitude), float(request.user.location.longitude)])
        for marker in activity.markers.all():
            markers.append([marker.description, float(marker.latitude), float(marker.longitude)])
    else:
        parent = request.user.location.get_parent(component_index)
        population.append([float(parent.latitude), float(parent.longitude)])
        all_users = User.objects.all().prefetch_related('location')
        for location in parent.children.all():
            total = location.get_population(all_users)
            highest_component = Location.components[location.highest_component_index()]
            members = activity.members.filter(**{'location__'+highest_component: getattr(location, highest_component)})
            population.append([getattr(location, highest_component), total.count(), members.count(), float(location.latitude), float(location.longitude)])

    users = users[:50]
    posts, page = Post.get_page(request, component_index, chosen_component, activity=activity)
    suggestion = None
    if request.user.character and request.user.character.presentable:
        suggestion = request.user.character.activity_suggestions.filter(activity=activity)
        if suggestion.exists():
            suggestion = suggestion.first()
    joined_chat = request.user.chat_rooms.filter(target_ct=Activity.content_type(), target_id=activity.id).exists()
    return render(request, 'activity/detail.html',
                  {'activity': activity,
                   'is_member': is_member,
                   'components': request.user.location.as_dict(),
                   'component_index': component_index,
                   'chosen_component': chosen_component,
                   'users': users,
                   'posts': posts,
                   'page': page,
                   'suggestion': suggestion,
                   'population': json.dumps(population) if population else None,
                   'markers': json.dumps(markers) if markers else None,
                   'chosen': request.GET.get('component_index'),
                   'joined_chat': joined_chat})



def category_detail(request, category_name):
    category = get_object_or_404(Category, translations__language_code=request.LANGUAGE_CODE, translations__name=category_name)
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = getattr(request.user.location, Location.components[component_index])
    posts, page = Post.get_page(request, component_index, chosen_component, category=category)
    return render(request, 'activity/category_detail.html', dict(category=category, posts=posts, chosen_component=chosen_component, component_index=component_index, page=page))


def join(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    activity.members.add(request.user)
    return HttpResponseRedirect(activity.get_absolute_url())


def leave(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    activity.members.remove(request.user)
    room_query = request.user.chat_rooms.filter(target_ct=Activity.content_type(), target_id=activity.id)
    if room_query.exists():
        room_query.first().members.remove(request.user)
    return HttpResponseRedirect(activity.get_absolute_url())


def category_list(request):
    #categories = Category.objects.annotate(count=Count('activities')).filter(count__gt=0) #TODO lieber visible?
    categories = Category.objects.prefetch_related('activities').filter(visible=True)
    return render(request, 'activity/category_list.html', dict(categories=categories))


def activity_list(request):
    component_index = int(request.GET.get('component_index', 3))
    search_string = request.GET.get('search_string')
    chosen_component = getattr(request.user.location, Location.components[component_index])
    if component_index == 3:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__city=chosen_component))).order_by('-count', '-pk')
    elif component_index == 2:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__county=chosen_component))).order_by('-count', '-pk')
    elif component_index == 1:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__state=chosen_component))).order_by('-count', '-pk')
    else:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__country=chosen_component))).order_by('-count', '-pk')
    if search_string:
        activities = activities.filter(translations__name__icontains=search_string)
    activities, page = paginate(activities, request, 12)
    return render(request, 'activity/activity_list.html',
                  {'activities': activities,
                   'component_index': component_index,
                   'components': request.user.location.as_dict(),
                   'search_string': search_string})
                   
                   
def no_source(request):
    return render(request, 'activity/no_source.html')
         
