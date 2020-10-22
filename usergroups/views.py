from django.shortcuts import render
from activity.models import Category
from django.contrib.auth.decorators import login_required
from .forms import GroupForm
from .models import UserGroup
from account.models import Location, User
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from wall.models import Post


@login_required
def group_list(request, id=None):
    component_index = int(request.GET.get('component_index', 3))
    if id:
        category = Category.objects.get(id=id)
        component = Location.components[component_index]
        groups = [group for group in category.groups.all() if group.admin.location.equal_to(request.user.location, component)]
        return render(request, 'usergroups/category_group_list.html', dict(category=category, component_index=component_index, groups=groups))
    else:
        return render(request, 'usergroups/user_group_list.html')


@login_required
def group_detail(request, id):
    group = UserGroup.objects.get(id=id)
    is_in_group = request.user in group.members.all()
    if not group.public and not is_in_group:
        return HttpResponseForbidden()
    posts = Post.objects.filter(target_ct=UserGroup.content_type(), target_id=group.id)
    return render(request, 'usergroups/group_detail.html', dict(group=group, is_member=is_in_group, posts=posts))


@login_required
def edit_group(request, id):
    group = UserGroup.objects.get(id=id)
    if request.user != group.admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        form.edit_mode = True
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = GroupForm(instance=group, initial=dict(admin=request.user, category=group.category.name))
    return render(request, 'usergroups/edit_group.html', dict(group=group, form=form))


@login_required
def create_group(request, id):
    category = Category.objects.get(id=id)
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.category = category
            group.admin = request.user
            group.save()
            return render(request, 'usergroups/group_created.html', dict(group=group))
    else:
        form = GroupForm(initial=dict(public=True, category=category.name, admin=request.user.username))

    return render(request, 'usergroups/create_group.html', dict(category=category, form=form))


@login_required
def delete_group(request, id):
    group = UserGroup.objects.get(id=id)
    if request.user != group.admin:
        return HttpResponseForbidden()
    group.delete()
    return render(request, 'usergroups/group_deleted.html', dict(group=group))


@login_required
def leave_group(request, id):
    group = UserGroup.objects.get(id=id)
    if request.user in group.members.all():
        if request.user == group.admin:
            return HttpResponse('Sie sind der Gruppenadmin. Bitte legen Sie zunächst einen neuen Admin fest oder löschen Sie die Gruppe.')
        group.members.remove(request.user)
        return HttpResponseRedirect(group.get_absolute_url())
    return HttpResponseForbidden()


@login_required
def kick_out(request, group_id, user_id):
    group = UserGroup.objects.get(id=group_id)
    user = User.objects.get(id=user_id)
    if request.user != group.admin or user not in group.members.all():
        return HttpResponseForbidden()
    group.members.remove(user)
    return HttpResponseRedirect(request.build_absolute_uri(f"/usergroups/edit_group/{group.id}"))
