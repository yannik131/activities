from shared.shared import paginate
from django.shortcuts import render, get_object_or_404
from activity.models import Category
from .forms import GroupForm
from .models import UserGroup
from account.models import Location, User
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from wall.models import Post
from django.utils.translation import gettext_lazy as _
from account.views import handler403
from notify.utils import notify
from django.contrib import messages


def group_list(request, id=None):
    if id:
        component_index = int(request.GET.get('component_index', 3))
        category = get_object_or_404(Category, id=id)
        chosen_component = request.user.location.get_component(Location.components[component_index])
        if component_index == 3:
            groups = UserGroup.objects.filter(admin__location__city=chosen_component, category=category)
        elif component_index == 2:
            groups = UserGroup.objects.filter(admin__location__county=chosen_component, category=category)
        elif component_index == 1:
            groups = UserGroup.objects.filter(admin__location__state=chosen_component, category=category)
        else:
            groups = UserGroup.objects.filter(admin__location__country=chosen_component, category=category)
        return render(request, 'usergroups/category_group_list.html', dict(category=category, component_index=component_index, groups=groups))
    else:
        return render(request, 'usergroups/user_group_list.html')


def group_detail(request, id):
    group = get_object_or_404(UserGroup, id=id)
    is_in_group = request.user in group.members.all()
    if not group.public and not is_in_group:
        return handler403(request)
    posts = Post.objects.filter(target_ct=UserGroup.content_type(), target_id=group.id)
    posts, page = paginate(posts, request)
    return render(request, 'usergroups/group_detail.html', dict(group=group, is_member=is_in_group, posts=posts, page=page))


def edit_group(request, id):
    group = get_object_or_404(UserGroup, id=id)
    if request.user != group.admin:
        return handler403(request)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group, files=request.FILES)
        form.edit_mode = True
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = GroupForm(instance=group, initial=dict(admin=request.user, category=group.category.name))
    return render(request, 'usergroups/edit_group.html', dict(group=group, form=form))


def create_group(request, id):
    category = get_object_or_404(Category, id=id)
    if request.method == 'POST':
        form = GroupForm(request.POST, files=request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.category = category
            group.admin = request.user
            group.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = GroupForm(initial=dict(public=True, category=category.name, admin=request.user.username))
    return render(request, 'usergroups/create_group.html', dict(category=category, form=form))


def delete_group(request, id):
    group = get_object_or_404(UserGroup, id=id)
    if request.user != group.admin:
        return handler403(request)
    group.delete()
    return render(request, 'usergroups/group_deleted.html', dict(group=group))


def leave_group(request, id):
    group = get_object_or_404(UserGroup, id=id)
    if request.user in group.members.all():
        if request.user == group.admin:
            messages.add_message(request, messages.INFO, _('Sie sind der Gruppenadmin. Bitte legen Sie zunächst einen neuen Admin fest oder löschen Sie die Gruppe.'))
        else:
            group.members.remove(request.user)
        return HttpResponseRedirect(group.get_absolute_url())
    return handler403(request)


def kick_out(request, group_id, user_id):
    group = get_object_or_404(UserGroup, id=group_id)
    user = get_object_or_404(User, id=user_id)
    if request.user != group.admin or user not in group.members.all():
        return handler403(request)
    group.members.remove(user)
    notify(user, group, "kicked_you_out")
    return HttpResponseRedirect(request.build_absolute_uri(f"/usergroups/edit_group/{group.id}"))
