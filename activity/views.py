from django.shortcuts import render
from .models import Activity, Category
from django.db.models import Count, Q
from account.models import Location
from wall.models import Post
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from shared.shared import log, paginate


def detail(request, activity_name):
    component_index = int(request.GET.get('component_index', 3))
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    is_member = request.user.activities.filter(pk=activity.id).exists()
    chosen_component = request.user.location.get_component(Location.components[component_index])
    if component_index == 3: # city
        users = activity.members.filter(location__city=chosen_component)
    elif component_index == 2:
        users = activity.members.filter(location__county=chosen_component)
    elif component_index == 1:
        users = activity.members.filter(location__state=chosen_component)
    else:
        users = activity.members.filter(location__country=chosen_component)
    users = users[:50]
    posts, page = Post.get_page(request, component_index, chosen_component, activity=activity)
    return render(request, 'activity/detail.html',
                  {'activity': activity,
                   'is_member': is_member,
                   'components': request.user.location.as_dict(),
                   'component_index': component_index,
                   'chosen_component': chosen_component,
                   'users': users,
                   'posts': posts,
                   'page': page})



def category_detail(request, category_name):
    category = get_object_or_404(Category, translations__language_code=request.LANGUAGE_CODE, translations__name=category_name)
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
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
    categories = Category.objects.all()
    return render(request, 'activity/category_list.html', dict(categories=categories))


def activity_list(request, search_string=None):
    component_index = int(request.GET.get('component_index', 3))
    component = Location.components[component_index]
    chosen_component = request.user.location.get_component(component)
    if component_index == 3:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__city=chosen_component))).order_by('-count')
    elif component_index == 2:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__county=chosen_component))).order_by('-count')
    elif component_index == 1:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__state=chosen_component))).order_by('-count')
    else:
        activities = Activity.objects.annotate(count=Count('members', filter=Q(members__location__country=chosen_component))).order_by('-count')
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
         
