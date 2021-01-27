from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Activity, Category
from django.db.models import Count, Q
from account.models import Location
from wall.models import Post
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
import json


@login_required
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


@login_required
def category_detail(request, category_name):
    category = get_object_or_404(Category, translations__language_code=request.LANGUAGE_CODE, translations__name=category_name)
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
    posts, page = Post.get_page(request, component_index, chosen_component, category=category)
    return render(request, 'activity/category_detail.html', dict(category=category, posts=posts, chosen_component=chosen_component, component_index=component_index, page=page))


@login_required
def join(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    activity.members.add(request.user)
    return HttpResponseRedirect(activity.get_absolute_url())


@login_required
def leave(request, activity_name):
    activity = get_object_or_404(Activity, translations__language_code=request.LANGUAGE_CODE, translations__name=activity_name)
    activity.members.remove(request.user)
    return HttpResponseRedirect(activity.get_absolute_url())


@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'activity/category_list.html', dict(categories=categories))


@login_required
def activity_list(request):
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
    
    return render(request, 'activity/activity_list.html',
                  {'activities': activities,
                   'component_index': component_index,
                   'components': request.user.location.as_dict()})
         
