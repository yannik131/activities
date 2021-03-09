from notify.utils import notify
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import VacancyForm, InvitationForm, ApplicationForm
from vacancies.models import Vacancy, Application, Invitation
from account.models import User
from django.http import HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from competitions.models import Tournament
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from account.views import handler403


@login_required
def create_vacancies(request, app_label, model, id):
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
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
    ct = get_object_or_404(ContentType, app_label=app_label, model=model)
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


@login_required
def delete_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if request.user != vacancy.target.admin:
        return handler403(request)
    vacancy.delete()
    return HttpResponseRedirect(vacancy.target.get_absolute_url())


@login_required
def delete_invitation(request, id):
    invitation = get_object_or_404(Invitation, id=id)
    if request.user not in [invitation.sender.admin, invitation.target]:
        return handler403(request)
    invitation.delete()
    return HttpResponseRedirect(request.build_absolute_uri("/vacancies/application_list/"))


@login_required
def accept_invitation(request, id):
    invitation = get_object_or_404(Invitation, id=id)
    if invitation.target != request.user:
        return handler403(request)
    invitation.sender.members.add(invitation.target)
    invitation.delete()
    return HttpResponseRedirect(invitation.sender.get_absolute_url())


@login_required
def apply_for_vacancy(request, id):
    vacancy = get_object_or_404(Vacancy, id=id)
    if not request.user.birth_year:
        #TODO: messages
        return HttpResponseRedirect(request.user.get_absolute_url())
    if not request.user.satisfies_requirements_of(vacancy):
        return handler403(request, _('Sie erfüllen die nötigen Voraussetzungen der Leerstelle (Ort, Alter und/oder Geschlecht) nicht. <a href=\"{link}\">Zurück</a>').format(link=vacancy.target.get_absolute_url()))
    elif request.user.applications.filter(vacancy=vacancy).exists():
        return handler403(request, _('Sie haben sich bereits beworben.'))
    elif type(vacancy.target) is Tournament and vacancy.target.application_deadline < timezone.now():
        return handler403(request, _('Die Anmeldefrist ist bereits abgelaufen. <a href=\"{link}\">Zurück</a>').format(link=vacancy.target.get_absolute_url()))
    if request.user in vacancy.target.members.all():
        return handler403(request, _('Sie sind bereits Mitglied.'))
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
    vacancy = get_object_or_404(Vacancy, id=id)
    if request.user == vacancy.target.admin or request.user in vacancy.target.members.all():
        return render(request, 'vacancies/review_vacancy.html', dict(vacancy=vacancy))
    return handler403(request)


@login_required
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


@login_required
def decline_application(request, id):
    application = get_object_or_404(Application, id=id)
    if request.user != application.vacancy.target.admin or application.status != 'pending':
        return handler403(request)
    application.status = 'declined'
    application.save()
    return HttpResponseRedirect(application.vacancy.get_absolute_url())


@login_required
def delete_application(request, id):
    application = get_object_or_404(Application, id=id)
    if request.user == application.vacancy.target.admin and application.status == 'declined' or request.user == application.user and application.status != 'declined':
        application.delete()
        if request.user == application.vacancy.target.admin:
            return HttpResponseRedirect(application.vacancy.get_absolute_url())
        elif request.user == application.user:
            return HttpResponseRedirect(request.user.get_absolute_url())
    return handler403(request)


@login_required
def application_list(request):
    invitations = Invitation.objects.filter(target_ct=User.content_type(), target_id=request.user.id)
    return render(request, 'vacancies/application_list.html', dict(invitations=invitations))
