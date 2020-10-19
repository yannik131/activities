from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .forms import VacancyForm, InvitationForm, ApplicationForm
from vacancies.models import Vacancy, Application, Invitation
from account.models import User
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType


@login_required
def create_vacancies(request, app_label, model, id):
    ct = ContentType.objects.get(app_label=app_label, model=model)
    target = ct.get_object_for_this_type(pk=id)
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        form.instance.target = target
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(target.get_absolute_url())
    else:
        form = VacancyForm()
    return render(request, 'vacancies/create_vacancies.html', dict(form=form, target=target))


@login_required
def create_invitation(request, app_label, model, id):
    ct = ContentType.objects.get(app_label=app_label, model=model)
    sender = ct.get_object_for_this_type(pk=id)
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        form.instance.sender = sender
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(sender.get_absolute_url())
    else:
        form = InvitationForm()
    return render(request, 'vacancies/create_invitation.html', dict(form=form, sender=sender))


@login_required
def edit_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user != vacancy.target.admin:
        return HttpResponseForbidden()
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(vacancy.target.get_absolute_url())
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, 'vacancies/edit_vacancy.html', dict(form=form, vacancy=vacancy))


@login_required
def delete_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user != vacancy.target.admin:
        return HttpResponseForbidden()
    vacancy.delete()
    return HttpResponseRedirect(vacancy.target.get_absolute_url())


@login_required
def delete_invitation(request, id):
    invitation = Invitation.objects.get(id=id)
    if request.user != invitation.sender.admin:
        return HttpResponseForbidden()
    invitation.delete()
    return HttpResponseRedirect(invitation.target.get_absolute_url())


@login_required
def accept_invitation(request, id):
    invitation = Invitation.objects.get(id=id)
    if invitation.target != request.user:
        return HttpResponseForbidden()
    invitation.sender.members.add(invitation.target)
    invitation.delete()
    return HttpResponseRedirect(invitation.sender.get_absolute_url())


@login_required
def apply_for_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if not request.user.satisfies_requirements_of(vacancy):
        return HttpResponseForbidden(f'Sie erfüllen die nötigen Voraussetzungen der Leerstelle (Ort, Alter und/oder Geschlecht) nicht. <a href=\"{vacancy.target.get_absolute_url()}\">Zurück</a>')
    elif request.user.applications.filter(vacancy=vacancy).exists():
        return HttpResponseForbidden('Sie haben sich bereits beworben.')
    if request.method == 'POST':
        form = ApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.vacancy = vacancy
            application.user = request.user
            application.save()
            return HttpResponseRedirect(vacancy.target.get_absolute_url())
    else:
        form = ApplicationForm()
    return render(request, 'vacancies/apply_for_vacancy.html', dict(form=form, vacancy=vacancy))


@login_required
def review_vacancy(request, id):
    vacancy = Vacancy.objects.get(id=id)
    if request.user not in vacancy.target.members.all():
        return HttpResponseForbidden()
    return render(request, 'vacancies/review_vacancy.html', dict(vacancy=vacancy))


@login_required
def accept_application(request, id):
    application = Application.objects.get(id=id)
    if request.user != application.vacancy.target.admin or application.status != 'pending':
        return HttpResponseForbidden()
    application.vacancy.target.members.add(application.user)
    application.accepted = True
    if not application.vacancy.persistent:
        application.vacancy.delete()
    return HttpResponseRedirect(application.vacancy.target.get_absolute_url())


@login_required
def decline_application(request, id):
    application = Application.objects.get(id=id)
    if request.user != application.vacancy.target.admin or application.status != 'pending':
        return HttpResponseForbidden()
    application.status = 'declined'
    application.save()
    return HttpResponseRedirect(application.vacancy.get_absolute_url())


@login_required
def delete_application(request, id):
    application = Application.objects.get(id=id)
    if request.user == application.vacancy.target.admin and application.status == 'declined' or request.user == application.user and application.status != 'declined':
        application.delete()
        if request.user == application.vacancy.target.admin:
            return HttpResponseRedirect(application.vacancy.get_absolute_url())
        elif request.user == application.user:
            return HttpResponseRedirect(request.user.get_absolute_url())
    return HttpResponseForbidden()


@login_required
def application_list(request):
    invitations = Invitation.objects.filter(target_ct=User.content_type(), target_id=request.user.id)
    return render(request, 'vacancies/application_list.html', dict(invitations=invitations))
