from notify.utils import notify
from django.shortcuts import render, get_object_or_404
from .forms import VacancyForm, InvitationForm, ApplicationForm
from vacancies.models import Vacancy, Application, Invitation
from account.models import User
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from competitions.models import Tournament
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from account.views import handler403, handler404
from django.contrib import messages
from django.urls import reverse


def create_vacancies(request, app_label, model, id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
    try:
        target = ct.get_object_for_this_type(pk=id)
    except:
        return handler404(request)
    if request.method == 'POST':
        form = VacancyForm(request.POST)
        form.instance.target = target
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(target.get_absolute_url())
    else:
        form = VacancyForm()
    return render(request, 'vacancies/create_vacancies.html', dict(form=form, target=target))


def create_invitation(request, app_label, model, id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
    try:
        sender = ct.get_object_for_this_type(pk=id)
    except:
        return handler404(request)
    if request.method == 'POST':
        form = InvitationForm(request.POST)
        form.instance.sender = sender
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(sender.get_absolute_url())
    else:
        form = InvitationForm()
    return render(request, 'vacancies/create_invitation.html', dict(form=form, sender=sender))


def edit_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if request.user != vacancy.target.admin:
        return handler403(request)
    if request.method == 'POST':
        form = VacancyForm(request.POST, instance=vacancy)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(vacancy.target.get_absolute_url())
    else:
        form = VacancyForm(instance=vacancy)
    return render(request, 'vacancies/edit_vacancy.html', dict(form=form, vacancy=vacancy))


def delete_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if request.user != vacancy.target.admin:
        return handler403(request)
    vacancy.delete()
    return HttpResponseRedirect(vacancy.target.get_absolute_url())


def delete_invitation(request, id):
    invitation = get_object_or_404(Invitation, id=id)
    if request.user not in [invitation.sender.admin, invitation.target]:
        return handler403(request)
    invitation.delete()
    if invitation.sender_ct != User.content_type():
        return HttpResponseRedirect(invitation.sender.get_absolute_url())
    return HttpResponseRedirect(request.build_absolute_uri("/vacancies/application_list/"))


def accept_invitation(request, id):
    invitation = get_object_or_404(Invitation, id=id)
    if invitation.target != request.user:
        return handler403(request)
    invitation.sender.members.add(invitation.target)
    invitation.delete()
    return HttpResponseRedirect(invitation.sender.get_absolute_url())


def apply_for_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if not request.user.birth_year:
        messages.add_message(request, messages.INFO, _('Bitte ergänzen Sie Ihr Profil (Geburtsjahr und Geschlecht), um sich bewerben zu können.'))
        return HttpResponseRedirect(reverse('account:edit'))
        
    elif not request.user.satisfies_requirements_of(vacancy):
        messages.add_message(request, messages.INFO, _('Sie erfüllen die Voraussetzungen der Leerstelle nicht.'))
        
    elif request.user.applications.filter(vacancy=vacancy).exists():
        messages.add_message(request, messages.INFO, _('Sie haben sich bereits beworben.'))
        
    elif type(vacancy.target) is Tournament and vacancy.target.application_deadline < timezone.now():
        messages.add_message(request, messages.INFO, _('Die Anmeldefrist ist bereits abgelaufen.'))
        
    elif request.user in vacancy.target.members.all():
        messages.add_message(request, messages.INFO, _('Sie sind bereits Mitglied.'))
        
    else:
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
    return HttpResponseRedirect(vacancy.target.get_absolute_url())


def review_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if request.user == vacancy.target.admin or request.user in vacancy.target.members.all():
        return render(request, 'vacancies/review_vacancy.html', dict(vacancy=vacancy))
    return handler403(request)


def accept_application(request, id):
    application = get_object_or_404(Application, id=id)
    if request.user != application.vacancy.target.admin or application.status != 'pending':
        return handler403(request)
    application.vacancy.target.members.add(application.user)
    notify(application.user, application.vacancy.target, "accepted_application")
    if not application.vacancy.persistent:
        application.vacancy.delete()
    application.delete()
    return HttpResponseRedirect(application.vacancy.target.get_absolute_url())


def decline_application(request, id):
    application = get_object_or_404(Application, id=id)
    if request.user != application.vacancy.target.admin or application.status != 'pending':
        return handler403(request)
    application.status = 'declined'
    application.save()
    return HttpResponseRedirect(application.vacancy.get_absolute_url())


def delete_application(request, id):
    application = get_object_or_404(Application, id=id)
    if request.user == application.vacancy.target.admin and application.status == 'declined' or request.user == application.user and application.status != 'declined':
        application.delete()
        if request.user == application.vacancy.target.admin:
            return HttpResponseRedirect(application.vacancy.get_absolute_url())
        elif request.user == application.user:
            return HttpResponseRedirect(request.user.get_absolute_url())
    return handler403(request)


def application_list(request):
    invitations = Invitation.objects.filter(target_ct=User.content_type(), target_id=request.user.id)
    return render(request, 'vacancies/application_list.html', dict(invitations=invitations))
