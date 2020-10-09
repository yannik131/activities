from django.shortcuts import render
from activity.models import Category
from django.contrib.auth.decorators import login_required
from .forms import GroupForm
from vacancies.forms import VacancyForm, InvitationForm, ApplicationForm
from .models import UserGroup
from vacancies.models import Vacancy, Application, Invitation
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
    application_dict = dict([(a.vacancy.id, a.status) for a in request.user.applications.all()])
    if is_in_group:
        vacancies = group.vacancies.all()
    posts = Post.objects.filter(target_ct=UserGroup.content_type(), target_id=group.id)
    return render(request, 'usergroups/group_detail.html', dict(group=group, application_dict=application_dict, is_member=is_in_group, posts=posts))


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
    return HttpResponseRedirect(group.get_absolute_url())


@login_required
def create_vacancies(request, id):
    group = UserGroup.objects.get(id=id)
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        form.instance.target = group
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = VacancyForm()
    return render(request, 'usergroups/create_vacancies.html', dict(form=form, group=group))


@login_required
def create_invitation(request, id):
    group = UserGroup.objects.get(id=id)
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        form.instance.group = group
        if form.is_valid():
            invitation = form.save()
            return HttpResponseRedirect(group.get_absolute_url())
    else:
        form = InvitationForm()
    return render(request, 'usergroups/create_invitation.html', dict(form=form, group=group))


@login_required
def edit_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user != vacancy.group.admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            vacancy = form.save()
            return HttpResponseRedirect(vacancy.group.get_absolute_url())
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, 'usergroups/edit_vacancy.html', dict(form=form, vacancy=vacancy))


@login_required
def delete_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user != vacancy.group.admin:
        return HttpResponseForbidden()
    vacancy.delete()
    return HttpResponseRedirect(vacancy.group.get_absolute_url())


@login_required
def delete_invitation(request, id):
    invitation = Invitation.objects.get(id=id)
    if request.user != invitation.group.admin:
        return HttpResponseForbidden()
    invitation.delete()
    return HttpResponseRedirect(invitation.group.get_absolute_url())


@login_required
def accept_invitation(request, id):
    invitation = Invitation.objects.get(id=id)
    if invitation.user != request.user:
        return HttpResponseForbidden()
    invitation.group.members.add(invitation.user)
    invitation.delete()
    return HttpResponseRedirect(request.build_absolute_uri('/usergroups/group_list/'))


@login_required
def apply_for_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if not request.user.satisfies_requirements_of(vacancy):
        return HttpResponseForbidden(f'Sie erfüllen die nötigen Voraussetzungen der Leerstelle (Ort, Alter und/oder Geschlecht) nicht. <a href=\"{vacancy.group.get_absolute_url()}\">Zurück</a>')
    elif request.user.applications.filter(vacancy=vacancy).exists():
        return HttpResponseForbidden('Sie haben sich bereits beworben.')
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.user = request.user
            application.save()
            return HttpResponseRedirect(vacancy.group.get_absolute_url())
    else:
        form = ApplicationForm()
    return render(request, 'usergroups/apply_for_vacancy.html', dict(form=form, vacancy=vacancy))


@login_required
def review_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user not in vacancy.group.members.all():
        return HttpResponseForbidden()
    return render(request, 'usergroups/review_vacancy.html', dict(vacancy=vacancy))


@login_required
def accept_application(request, id):
    application = Application.objects.get(id=id)
    if request.user != application.vacancy.group.admin or application.status != 'pending':
        return HttpResponseForbidden()
    application.vacancy.group.members.add(application.user)
    application.vacancy.delete()
    return HttpResponseRedirect(application.vacancy.group.get_absolute_url())


@login_required
def decline_application(request, id):
    application = Application.objects.get(id=id)
    if request.user != application.vacancy.group.admin or application.status != 'pending':
        return HttpResponseForbidden()
    application.status = 'declined'
    application.save()
    return HttpResponseRedirect(application.vacancy.get_absolute_url())


@login_required
def delete_application(request, id):
    application = Application.objects.get(id=id)
    if request.user == application.vacancy.group.admin and application.status == 'declined' or request.user == application.user and application.status != 'declined':
        application.delete()
        if request.user == application.vacancy.group.admin:
            return HttpResponseRedirect(application.vacancy.get_absolute_url())
        elif request.user == application.user:
            return HttpResponseRedirect(request.build_absolute_uri('/usergroups/group_list/'))
    return HttpResponseForbidden()