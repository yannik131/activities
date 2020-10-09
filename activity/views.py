from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Activity, Category
from account.models import Location
from wall.models import Post
from django.http import HttpResponseRedirect


@login_required
def detail(request, name):
    component_index = int(request.GET.get('component_index', 3))
    activity = Activity.objects.get(name=name)
    is_member = activity in request.user.activities.all()
    users = []
    for user in activity.members.all().exclude(username=request.user.username):
        if request.user.location.equal_to(user.location, Location.components[component_index]):
            users.append(user)
    chosen_component = request.user.location.get_component(Location.components[component_index])
    posts = []
    for post in Post.objects.filter(activity=activity):
        if request.user.location.equal_to(post.author.location, Location.components[component_index]):
            posts.append(post)
    return render(request, 'activity/detail.html',
                  {'activity': activity,
                   'is_member': is_member,
                   'components': request.user.location.as_dict(),
                   'component_index': component_index,
                   'chosen_component': chosen_component,
                   'users': users,
                   'posts': posts})


@login_required
def category_detail(request, id):
    category = Category.objects.get(id=id)
    posts = []
    component_index = int(request.GET.get('component_index', 3))
    chosen_component = request.user.location.get_component(Location.components[component_index])
    for post in Post.objects.filter(category=category):
        if post.author.location.equal_to(request.user.location, Location.components[component_index]):
            posts.append(post)
    return render(request, 'activity/category_detail.html', dict(category=category, posts=posts, chosen_component=chosen_component, component_index=component_index))


@login_required
def join(request, name):
    activity = Activity.objects.get(name=name)
    activity.members.add(request.user)
    return HttpResponseRedirect(activity.get_absolute_url())


@login_required
def leave(request, name):
    activity = Activity.objects.get(name=name)
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

    def contains(u):
        return request.user.location.equal_to(u.location, component)

    activities = []
    for activity in Activity.objects.all():
        count = len([u for u in activity.members.all() if contains(u)])
        activities.append((activity, count))
    activities = sorted(activities, key=lambda t: t[1], reverse=True)
    return render(request, 'activity/activity_list.html',
                  {'activities': activities,
                   'component_index': component_index,
                   'components': request.user.location.as_dict()})
